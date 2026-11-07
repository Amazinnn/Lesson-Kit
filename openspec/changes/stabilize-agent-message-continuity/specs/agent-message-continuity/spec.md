## Purpose

Defines the observable 消息连续性与极简发送队列 behavior for the Lesson Kit course workflow, preserving explicit data ownership, learning evidence and verifiable normal-entry outcomes.

## ADDED Requirements

### Requirement: Accepted messages stay in conversation

Accepted messages SHALL persist once in conversation history with captured submission context. Failure, stop and queue waiting SHALL NOT relocate or duplicate the original message. Unknown acceptance SHALL reconcile the same submission identity.

#### Scenario: An accepted turn fails

- **WHEN** a provider fails after accepting a message
- **THEN** the original message and actual partial output remain in conversation and no automatic retry entry is created

#### Scenario: The response is lost

- **WHEN** acceptance is uncertain and the user retries delivery
- **THEN** the original identity is reconciled without a second accepted operation

### Requirement: Pending presentation is minimal

The ordinary pending list SHALL show only message content, edit and delete controls. It SHALL contain no additional state fields, reorder or send-now controls. Existing configured running-send behavior SHALL remain usable through its settings entry.

#### Scenario: Long pending content is inspected

- **WHEN** several long messages are queued
- **THEN** their full content is readable and editable while only the specified ordinary controls appear

### Requirement: Stopping pauses pending dispatch

An explicit stop SHALL pause retained pending messages until explicit continuation. An abnormal restart SHALL retain never-started messages without dispatch. Ordinary execution failure SHALL NOT automatically retry the failed message and independent subsequent messages SHALL follow the existing continuation behavior.

#### Scenario: The user stops with queued messages

- **WHEN** a current turn is stopped with two messages pending
- **THEN** the messages remain paused until the user explicitly continues

#### Scenario: The app restarts

- **WHEN** pending messages had never begun before an abnormal exit
- **THEN** their content survives and automatic dispatch count is zero

### Requirement: Captured targets and recovery remain stable

Queued and retried messages SHALL use their original captured course and object context. An explicit failed-message retry SHALL use current edited text, linked retry identity and original context, without overwriting a newer composer draft. Waiting without evidence of failure SHALL remain a brief status with a stop operation.

#### Scenario: Navigation occurs during queue wait

- **WHEN** a message for question A waits while the user switches to question B
- **THEN** execution still targets question A

#### Scenario: No new output appears

- **WHEN** the provider remains active without output
- **THEN** a brief waiting state and stop control remain without repeated notices or speculative failure
