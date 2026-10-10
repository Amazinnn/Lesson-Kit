## ADDED Requirements

### Requirement: Bootstrap requires readable repository inputs

Bootstrap SHALL account for every existing file under the selected course's
subtree in the checked-out content repository. A file that cannot be decoded as
UTF-8 text or parsed as a JSON object SHALL NOT be dropped from the report; the
bootstrap report SHALL list each unreadable file with its repository-relative
path and reason.

An unreadable file SHALL implicate a pool entity when that entity's id appears
in the file name or in the file's bytes decoded with replacement. Bootstrap
SHALL NOT create a canonical file for an implicated entity. When no readable
repository file already establishes that entity, bootstrap SHALL report it as
blocked while naming the implicating file, and SHALL leave the pool row and any
mirror state untouched.

Entities that no unreadable file implicates SHALL bootstrap normally, so one
unreadable file never prevents the rest of the course from being established.

#### Scenario: An unreadable renamed copy blocks only the implicated entity

- **GIVEN** an untracked knowledge point `c02-ch01-kp-001` and an unreadable JSON file under the course subtree whose bytes name that entity id
- **WHEN** bootstrap runs
- **THEN** the report lists the unreadable file with its path and reason
- **AND** the entity is reported blocked with no canonical file created, its pool row and mirror state untouched
- **AND** every other entity is bootstrapped at revision 1

#### Scenario: An unreadable file that names no entity is reported without blocking

- **GIVEN** an unreadable file whose name and replacement-decoded bytes name no pool entity id
- **WHEN** bootstrap runs
- **THEN** the report lists that file with its reason
- **AND** all unimplicated entities are bootstrapped

#### Scenario: A clean subtree reports no unreadable files

- **GIVEN** the course subtree contains only readable entity JSON documents and valid deletion requests
- **WHEN** bootstrap runs
- **THEN** the report contains no unreadable-file entries
