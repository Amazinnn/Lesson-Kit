"""Isolated mixed-part execution, disclosure and immutable submission checks."""

import json
import unittest

from tests.workbench.fixtures import WorkspaceFixture
from workbench.data import active_practice, part_practice, part_grading
from workbench.domain.part_grading import validate
from workbench.server import api


class PartPracticeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = WorkspaceFixture()
        self.pool = api._pool_for({'path': str(self.fixture.ws), 'db': 'pool/dmath.db',
                                  'active_course': 'dmath', 'active_chapter': 'ch06'})
        self.problem_id = 'dmath-ch06-prob-001'
        self.parts = [
            {'id': 'choice', 'type': 'single_choice', 'prompt': 'Pick', 'options': ['a', 'b'], 'answer_key': 'a'},
            {'id': 'calc', 'type': 'calculation', 'prompt': 'Calculate', 'reference_answer': '42', 'reference_reasoning': 'secret calc'},
            {'id': 'proof', 'type': 'proof', 'prompt': 'Prove', 'reference_reasoning': 'secret proof'}]
        self.pool.connect().execute('UPDATE problems SET parts=? WHERE problem_id=?',
                                   (json.dumps(self.parts), self.problem_id))
        self.pool.commit()
        self.run = active_practice.create(self.pool, {
            'source_kind': 'quick', 'kp_ids': ['dmath-ch06-kp-001'], 'practice_mode': 'exam',
            'rating_mode': 'off', 'reveal_timing': 'on_submit',
            'items': [{'item_type': 'problem', 'item_id': self.problem_id}]})
        self.context = active_practice.submission_context(self.run, 0)

    def tearDown(self):
        self.pool.close()
        self.fixture.cleanup()

    def save(self, part_id, **fields):
        return part_practice.save_draft(self.pool, self.run['execution_id'], 0, part_id,
                                        fields, context=self.context)

    def submit(self, part_id=None, request='one'):
        return part_practice.submit(self.pool, self.run['execution_id'], 0, request,
                                   part_id=part_id, context=self.context)

    def projected(self):
        return part_practice.project(self.pool, active_practice.current(self.pool))

    def test_partial_submission_locks_only_selected_part_and_replays(self):
        self.save('calc', answer='my original process')
        first = self.submit('calc')
        self.assertEqual(self.submit('calc')['attempt_ids'], first['attempt_ids'])
        self.assertTrue(self.submit('calc')['replay'])
        children = self.projected()['items'][0]['part_items']
        self.assertEqual([p['locked'] for p in children], [False, True, False])
        self.assertEqual(self.pool.attempt(first['attempt_ids'][0])['answer_text'], 'my original process')
        with self.assertRaises(active_practice.ActivePracticeConflict):
            self.save('calc', answer='replace')
        self.save('proof', answer='still editable')

    def test_stuck_keeps_process_and_discloses_only_its_reference(self):
        self.save('calc', answer='partial work', stuck=True)
        value = self.projected()
        text = json.dumps(value)
        self.assertIn('secret calc', text)
        self.assertNotIn('secret proof', text)
        self.assertNotIn('answer_key', text)
        self.submit('calc')
        child = self.projected()['items'][0]['part_items'][1]
        self.assertTrue(child['stuck'])
        self.assertEqual(child['answer'], 'partial work')

    def test_hidden_grade_is_omitted_from_all_parent_fields_until_final_submit(self):
        self.save('calc', answer='42 because …')
        attempt_id = self.submit('calc')['attempt_ids'][0]
        before = self.pool.attempt(attempt_id)
        part_grading.mutate(self.pool, attempt_id=attempt_id, problem_id=self.problem_id,
            part_id='calc', content_revision=self.context['content_revision'], expected_revision=0,
            operation_id='grade', payload={'answer_conclusion': 'correct', 'process_conclusion': 'wrong',
                'extracted_answer': '42', 'feedback': 'private feedback'}, validate=validate)
        hidden = self.projected()
        self.assertNotIn('private feedback', json.dumps(hidden))
        self.assertEqual(hidden['items'][0]['part_summary']['answer'], {})
        self.assertIsNone(hidden['items'][0]['part_items'][1]['grading'])
        done = active_practice.submit(self.pool, self.run['execution_id'], 'final', grade_answer=lambda *a: None)
        result = part_practice.project(self.pool, active_practice.get_run(self.pool, done['run_id']), completed=True)
        child = result['items'][0]['part_items'][1]
        self.assertEqual(child['grading']['payload']['process_conclusion'], 'wrong')
        self.assertEqual(self.pool.attempt(attempt_id), before)
        self.assertEqual(self.pool.connect().execute('SELECT COUNT(*) FROM problem_attempts').fetchone()[0], 3)

    def test_bad_batch_and_draft_have_zero_writes(self):
        self.save('calc', answer='saved')
        before = self.pool.connect().execute('SELECT COUNT(*) FROM problem_attempts').fetchone()[0]
        with self.assertRaises(active_practice.ActivePracticeError):
            self.submit('missing')
        with self.assertRaises(active_practice.ActivePracticeError):
            self.save('choice', choices=['missing'])
        self.assertEqual(self.pool.connect().execute('SELECT COUNT(*) FROM problem_attempts').fetchone()[0], before)

    def test_no_learning_effects_from_part_submissions(self):
        tables = ['problem_progress', 'learner_signals', 'schedule']
        tables = [t for t in tables if self.pool.connect().execute(
            'SELECT 1 FROM sqlite_master WHERE name=?', (t,)).fetchone()]
        before = {t: [tuple(r) for r in self.pool.connect().execute('SELECT * FROM ' + t)] for t in tables}
        self.save('choice', choices=['b'])
        self.submit()
        after = {t: [tuple(r) for r in self.pool.connect().execute('SELECT * FROM ' + t)] for t in tables}
        self.assertEqual(before, after)

    def test_stuck_draft_can_be_revised_but_reference_fact_persists(self):
        self.save('calc', stuck=True)
        self.save('calc', answer='I solved it')
        child = self.projected()['items'][0]['part_items'][1]
        self.assertFalse(child['stuck'])
        self.assertTrue(child['reference_viewed'])

    def test_legacy_draft_cannot_remove_a_submitted_sibling(self):
        self.save('calc', answer='immutable first')
        attempt_id = self.submit('calc')['attempt_ids'][0]
        with self.assertRaises(active_practice.ActivePracticeConflict):
            active_practice.save_draft(self.pool, self.run['execution_id'], 0,
                {'answer': 'stale page'}, context=self.context, sequence=99)
        self.assertTrue(self.projected()['items'][0]['part_items'][1]['locked'])
        self.assertEqual(self.submit('calc', request='again')['attempt_ids'], [attempt_id])

    def test_late_grading_after_final_submit_updates_original_without_new_attempt(self):
        self.save('calc', answer='42 because …')
        attempt_id = self.submit('calc')['attempt_ids'][0]
        done = active_practice.submit(self.pool, self.run['execution_id'], 'final', grade_answer=lambda *a: None)
        before = self.pool.attempt(attempt_id)
        attempts_before = self.pool.connect().execute('SELECT COUNT(*) FROM problem_attempts').fetchone()[0]
        first = part_grading.mutate(self.pool, attempt_id=attempt_id, problem_id=self.problem_id,
            part_id='calc', content_revision=self.context['content_revision'], expected_revision=0,
            operation_id='late-grade', payload={'answer_conclusion': 'correct', 'process_conclusion': 'wrong',
                'extracted_answer': '42', 'feedback': 'late feedback'}, validate=validate)
        self.assertEqual(first['revision'], 1)
        repeated = part_grading.mutate(self.pool, attempt_id=attempt_id, problem_id=self.problem_id,
            part_id='calc', content_revision=self.context['content_revision'], expected_revision=0,
            operation_id='late-grade', payload={'answer_conclusion': 'correct', 'process_conclusion': 'wrong',
                'extracted_answer': '42', 'feedback': 'late feedback'}, validate=validate)
        self.assertEqual(repeated, first)
        self.assertEqual(len(part_grading.list_revisions(self.pool, attempt_id)), 1)
        self.assertEqual(self.pool.attempt(attempt_id), before)
        self.assertEqual(self.pool.connect().execute('SELECT COUNT(*) FROM problem_attempts').fetchone()[0], attempts_before)
        result = part_practice.project(self.pool, active_practice.get_run(self.pool, done['run_id']), completed=True)
        self.assertEqual(result['items'][0]['part_items'][1]['grading']['payload']['feedback'], 'late feedback')

    def test_stale_content_and_revision_are_rejected_without_history_rewrite(self):
        self.save('calc', answer='42 because …')
        attempt_id = self.submit('calc')['attempt_ids'][0]
        first = part_grading.mutate(self.pool, attempt_id=attempt_id, problem_id=self.problem_id,
            part_id='calc', content_revision=self.context['content_revision'], expected_revision=0,
            operation_id='grade-one', payload={'answer_conclusion': 'correct'}, validate=validate)
        with self.assertRaises(ValueError):
            part_grading.mutate(self.pool, attempt_id=attempt_id, problem_id=self.problem_id,
                part_id='calc', content_revision=self.context['content_revision'], expected_revision=0,
                operation_id='grade-two', payload={'answer_conclusion': 'wrong'}, validate=validate)
        with self.assertRaises(ValueError):
            part_grading.mutate(self.pool, attempt_id=attempt_id, problem_id=self.problem_id,
                part_id='calc', content_revision=self.context['content_revision'] + 1, expected_revision=1,
                operation_id='grade-stale-content', payload={'answer_conclusion': 'wrong'}, validate=validate,
                actual_content_revision=lambda conn, problem: self.context['content_revision'])
        revisions = part_grading.list_revisions(self.pool, attempt_id)
        self.assertEqual(len(revisions), 1)
        self.assertEqual(revisions[0], first)


if __name__ == '__main__':
    unittest.main()
