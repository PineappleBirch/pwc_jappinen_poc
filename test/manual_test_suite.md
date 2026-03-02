# Manual Test Suite - Jäppinen Ltd. AI Chatbot PoC

A human-run test guide for validating the RAG chatbot against both service manuals.
Run each test by typing the **Query** into the app and checking that the **Expected content** appears in the response and that the cited **Source** is correct.

**Rating scale:**
- `PASS` - Answer contains expected content and cites the correct manual
- `FAIL` - Answer is wrong, refuses, or cites the wrong source

---

## How to Run

```bash
cd /Volumes/X10\ Pro/jappinen-ai-poc
source venv/bin/activate
python main.py
```

---

## Section 1: Out-of-Scope & Grounding

These tests verify the system refuses irrelevant queries and does not hallucinate.

| # | Query | Expected content | Source | Result |
|---|-------|-----------------|--------|--------|
| 1.1 | `How do I fix a car engine?` | Polite refusal | None | PASS |
| 1.2 | `What is the capital of France?` | Polite refusal | None | PASS |
| 1.3 | `Write me a poem about washing machines` | Polite refusal | None | PASS |

---

## Section 2: CLI Commands & Navigation

These tests validate the slash commands, manual filter, streaming output, and keyboard navigation.
Start a **fresh session** (`python main.py`) for each numbered sub-test below.

### 2.1 - Slash Commands

| # | Action | Expected behaviour | Result |
|---|--------|-------------------|--------|
| 2.1.1 | Type `/help` | Prints list of all available commands: `/help`, `/manuals`, `/filter`, `/clear`, `/last`, `quit`/`exit` | PASS |
| 2.1.2 | Type `/manuals` | Shows both loaded manuals with chunk counts, e.g. `technical-manual-w11663204-revb.pdf - N chunks` | PASS |
| 2.1.3 | Type `/unknowncommand` | Error message: unknown command, suggests `/help` | PASS |
| 2.1.4 | Type `/filter` (no argument) | Usage hint: `/filter maytag \| /filter midea \| /filter off` | PASS |
| 2.1.5 | Type `/clear` before any query | Confirmation: conversation history cleared | PASS |
| 2.1.6 | Type `/last` before any query | Message: no previous answer to display | PASS |

### 2.2 - Manual Filter

| # | Action | Expected behaviour | Result |
|---|--------|-------------------|--------|
| 2.2.1 | Type `/filter maytag` | Confirmation printed; prompt changes to `Mechanic [maytag]:` | PASS |
| 2.2.2 | With maytag filter active, ask `What does fault code F5E2 mean?` | Correct answer (Lid Lock Fault); sources only from Maytag manual | PASS |
| 2.2.3 | With maytag filter active, ask `What does error code E60 mean?` | Refusal or low-confidence warning - Midea content excluded by filter | PASS |
| 2.2.4 | Type `/filter off` | Confirmation printed; prompt returns to `Mechanic:` | PASS |
| 2.2.5 | Type `/filter midea` | Confirmation printed; prompt changes to `Mechanic [midea]:` | PASS |
| 2.2.6 | With midea filter active, ask `What does error code E60 mean?` | Correct answer (Motor does not rotate); sources only from Midea manual | PASS |
| 2.2.7 | With midea filter active, ask `What does fault code F5E2 mean?` | Refusal or low-confidence warning - Maytag content excluded by filter | PASS |

### 2.3 - `/last` and `/clear`

| # | Action | Expected behaviour | Result |
|---|--------|-------------------|--------|
| 2.3.1 | Ask any question, then type `/last` | Reprints the previous answer and sources without re-querying | PASS |
| 2.3.2 | Have a 2-turn conversation, then type `/clear`, then ask a follow-up like `What are the next steps?` | Follow-up fails to resolve (history was cleared) - gets a low-confidence or refusal response | PASS |

### 2.4 - Streaming & Keyboard Navigation

| # | Action | Expected behaviour | Result |
|---|--------|-------------------|--------|
| 2.4.1 | Ask any question | Answer streams token-by-token to the terminal (visible word-by-word output, not all at once) | PASS |
| 2.4.2 | Type a query, press ↑ arrow | Previous query recalled into the input line | PASS |
| 2.4.3 | Type a query, use ← → arrows | Cursor moves within the input line | PASS |

---

## Section 3: Maytag - Fault Codes

Manual: `technical-manual-w11663204-revb.pdf`

| # | Query | Expected content | Source | Result |
|---|-------|-----------------|--------|-------|
| 3.1 | `What does fault code F5E2 mean?` | Lid Lock Fault | Maytag | PASS |
| 3.2 | `What does fault code F5E1 mean?` | Lid Switch Fault | Maytag | PASS |
| 3.3 | `What does fault code F9E1 mean?` | Long Drain | Maytag | PASS |
| 3.4 | `What does fault code F8E1 mean?` | Long Fill | Maytag | PASS |
| 3.5 | `What does fault code F8E6 mean?` | No Fill | Maytag | PASS |
| 3.6 | `What does fault code F8E3 mean?` | Overflow Condition | Maytag | PASS |
| 3.7 | `What does fault code F8E5 mean?` | Hot and Cold reversed | Maytag | PASS |
| 3.8 | `What does fault code F7E1 mean?` | Basket Speed Sensor Fault | Maytag | PASS |
| 3.9 | `What does fault code F7E5 mean?` | Shifter Fault | Maytag | PASS |
| 3.10 | `What does fault code F7E7 mean?` | Motor Unable to Reach Target RPM | Maytag | PASS |
| 3.11 | `What does fault code F3E1 mean?` | Pressure Sensor Fault | Maytag | PASS |
| 3.12 | `What does fault code F1E1 mean?` | Main Control Fault | Maytag | PASS |
| 3.13 | `What does fault code F0E2 mean?` | Over Suds Condition | Maytag | PASS |
| 3.14 | `What does fault code F0E5 mean?` | Off-Balance Load Detected | Maytag | PASS |
| 3.15 | `What does fault code F0E0 mean?` | No Fault (normal state) | Maytag | PASS |

---

## Section 4: Maytag - Components & Specifications

| # | Query | Expected content | Source | Result |
|---|-------|-----------------|--------|--------|
| 4.1 | `What is the resistance of the hot water inlet valve on the Maytag?` | 890–1,300 ohms | Maytag | PASS |
| 4.2 | `What is the resistance of the drain pump motor on the Maytag?` | 14–25 ohms | Maytag | PASS |
| 4.3 | `What is the resistance of the lid lock solenoid on the Maytag?` | 85–155 ohms | Maytag | PASS |
| 4.4 | `What is the resistance of the shifter motor on the Maytag?` | 2,000–3,500 ohms | Maytag | PASS |
| 4.5 | `What is the resistance of the motor windings on the Maytag?` | 3.5–6 ohms (CCW and CW windings) | Maytag | PASS |
| 4.6 | `What is the thermistor resistance at 68°F (20°C) on the Maytag?` | ~62 kΩ (corrected from 9.67 kΩ - verified against PDF) | Maytag | PASS |
| 4.7 | `What is the thermistor resistance at 32°F (0°C) on the Maytag?` | ~163 kΩ (corrected from 31.38 kΩ - verified against PDF) | Maytag | PASS |
| 4.8 | `What is the thermistor resistance at 104°F (40°C)?` | ~27 kΩ (corrected from 3.50 kΩ - verified against PDF) | Maytag | PASS |
| 4.9 | `How do I test the run capacitor on the Maytag motor?` | Measure across capacitor terminals with ohmmeter; steady increase in resistance = OK; shorted or open = replace | Maytag | PASS |
| 4.10 | `What is the voltage and frequency of the Maytag washer?` | 120 VAC, 60 Hz | Maytag | PASS |
| 4.11 | `What is the motor RPM on the Maytag washer?` | 700 RPM | Maytag | PASS |
| 4.12 | `What is the capacity of the Maytag washer?` | 3.5 cu ft (DOE); 4 cu ft (IEC) | Maytag | PASS |
| 4.13 | `What type of motor does the Maytag use?` | Bi-directional PSC (Permanent Split Capacitor), 120 VAC | Maytag | PASS |
| 4.14 | `What is the water pressure range for the Maytag?` | 20–125 PSI | Maytag | PASS |

---

## Section 5: Maytag - Diagnostics, Troubleshooting & Disassembly

| # | Query | Expected content | Source | Result |
|---|-------|-----------------|--------|--------|
| 5.1 | `How do I enter service diagnostic mode on the Maytag?` | Unplug washer; plug back in; immediately press POWER button | Maytag | PASS |
| 5.2 | `How do I exit diagnostic mode on the Maytag?` | Hold START for 3 seconds, or auto-exit after 5 minutes | Maytag | PASS |
| 5.3 | `How do I run a Low Spin test on the Maytag?` | Status LEDs 8 1; spins 0–500 RPM; lid closed and locked; basket empty | Maytag | FAIL |
| 5.4 | `How do I run the Lid Lock test in Manual Overview mode?` | Status LEDs 4 1; lid must be closed; only unlocks when basket RPM is 0 | Maytag | PASS |
| 5.5 | `How do I run a Gentle Agitation test on the Maytag?` | Status LEDs 8 2 1; lid closed and locked; basket must be empty | Maytag | PASS |
| 5.6 | `The Maytag washer will not fill with water` | Check valve (TEST #2), main control (TEST #1), plugged inlet filter | Maytag | PASS |
| 5.7 | `The Maytag washer will not spin` | Lid lock (TEST #8), shifter (TEST #3a), motor relay and motor (TEST #3b) | Maytag | PASS |
| 5.8 | `The Maytag washer will not drain` | Drain pump (TEST #7), clogged drain hose | Maytag | PASS |
| 5.9 | `The Maytag washer fills with the wrong temperature water` | Thermistor (TEST #5), valves (TEST #2); check for hot/cold reversed (F8E5) | Maytag | PASS |
| 5.10 | `How do I remove the top panel on the Maytag?` | Remove knobs; remove 2 T20 security screws from front edge; lift and release from clips | Maytag | PASS |
| 5.11 | `How do I remove the lid lock on the Maytag?` | Disconnect J15 connector (2 locking tabs); remove 2 × 1/4" hex screws; remove bezel; verify O-rings on reinstall | Maytag | PASS |
| 5.12 | `How do I remove the drive motor on the Maytag?` | Disconnect wire harness; remove 2 bolts securing motor to transmission housing; support motor on second bolt | Maytag | PASS |
| 5.13 | `How do I remove the shifter on the Maytag?` | Disconnect J2 connector (2 locking tabs); remove 2 Phillips head screws | Maytag | PASS |
| 5.14 | `Does the Maytag drain pump have serviceable parts?` | No - replaced as complete assembly; filter accessible for cleaning | Maytag | PASS |
| 5.15 | `How long should the Maytag shifter take to change position?` | 4–15 seconds | Maytag | PASS |

---

## Section 6: Midea - Malfunction Codes

Manual: `LAD-Front-Loading-Service-Manual-L11.pdf`

| # | Query | Expected content | Source | Result |
|---|-------|-----------------|--------|--------|
| 6.1 | `What does error code E60 mean on the Midea?` | Motor failed to start 5 times; loose/damaged PCB or motor terminals | Midea | PASS |
| 6.2 | `What does error code E61 mean on the Midea?` | Motor speed abnormal during rotation | Midea | PASS |
| 6.3 | `What does error code E62 mean on the Midea?` | SCR on PCB damaged | Midea | PASS |
| 6.4 | `What does error code E30 mean on the Midea?` | Door cannot be locked | Midea | PASS |
| 6.5 | `What does error code E50 mean on the Midea?` | Motor inverter PCB abnormal / Voltage abnormality | Midea | PASS |
| 6.6 | `What does error code E80 mean on the Midea?` | No communication between main control and display panel | Midea | PASS |
| 6.7 | `What does error code E10 mean on the Midea?` | Water inlet problem during wash cycle | Midea | PASS |
| 6.8 | `What does error code E12 mean on the Midea?` | Water level exceeded / Overflow | Midea | PASS |
| 6.9 | `What does error code E21 mean on the Midea?` | Long drain / Drain timeout after 6 minutes | Midea | PASS |
| 6.10 | `What does error code E33 mean on the Midea?` | Water level sensor problem / abnormal frequency | Midea | PASS |
| 6.11 | `What does error code E64 mean on the Midea?` | Motor inverter PCB error (BLDC models only) | Midea | PASS |

---

## Section 7: Midea - Components, Troubleshooting & Disassembly

| # | Query | Expected content | Source | Result |
|---|-------|-----------------|--------|--------|
| 7.1 | `What is the resistance of the water inlet valve on the Midea?` | 3–6 kΩ | Midea | PASS |
| 7.2 | `What is the resistance of the drain pump on the Midea?` | 150–250 ohms | Midea | PASS |
| 7.3 | `What is the acceptable voltage range for the Midea 220V model?` | Not less than 165V and not more than 275V | Midea | PASS |
| 7.4 | `What target RPM should the Midea motor reach?` | 400 RPM | Midea | PASS |
| 7.5 | `The Midea washer door won't lock` | Check door alignment; test door lock resistance (100–300Ω); error code E30 | Midea | PASS |
| 7.6 | `The Midea drum is not rotating` | Check motor terminals; verify connector seated; error code E60 | Midea | PASS |
| 7.7 | `The Midea washer is not draining` | Check drain hose; clean pump filter; check pump resistance (150–250Ω); error code E21 | Midea | PASS |
| 7.8 | `How do I remove the motor on the Midea?` | Remove rear cover (4 screws); remove pulley bolt; disconnect connector; remove 2 mounting screws; pull upward | Midea | PASS |

---

## Section 8: Conversation History & Follow-ups

These tests validate multi-turn conversations and query rewriting. Start a **fresh session** for each sub-test.

### 8.1 - Maytag Fault Code Follow-up

| Turn | Query | Expected content | Result |
|------|-------|-----------------|--------|
| 1 | `What does fault code F5E2 mean?` | Lid Lock Fault | PASS |
| 2 | `How do I test the component responsible for this fault?` | Lid lock solenoid resistance 85–155Ω; J15 connector; lid must be closed; basket RPM must be 0 | PASS |
| 3 | `What are the steps to replace it?` | Unplug washer; replace main control; reassemble; calibrate; run Quick Overview Test | PASS |

### 8.2 - Midea Motor Error Follow-up

| Turn | Query | Expected content | Result |
|------|-------|-----------------|--------|
| 1 | `Explain malfunction code E60` | Motor does not rotate; check motor terminals and PCB terminals | PASS |
| 2 | `How do I check the motor terminals?` | Remove rear cover (4 screws); check for loose or corroded connections | PASS |
| 3 | `What are the next steps if that doesn't fix it?` | Replace motor if defective; check PCB terminal connections | FAIL |

### 8.3 - Cross-Manual Drain Pump Confusion

| Turn | Query | Expected content | Result |
|------|-------|-----------------|--------|
| 1 | `What does fault code F9E1 mean?` | Long Drain (Maytag) | PASS |
| 2 | `What is the resistance of the drain pump?` | Maytag value (14–25Ω) - **not** Midea value (150–250Ω) | PASS |

> **Note:** Test 8.3 verifies the system maintains context between turns and does not confuse drain pump specs between manuals. Both manuals cover drain pumps but resistance ranges differ significantly.

---

## Test Run Summary

| Section | Tests | Pass | Fail |
|---------|-------|------|------|
| 1. Out-of-Scope & Grounding | 3 | 3 | |
| 2. CLI Commands & Navigation | 16 | 16 | |
| 3. Maytag - Fault Codes | 15 | 15 | |
| 4. Maytag - Components & Specifications | 14 | 14 | |
| 5. Maytag - Diagnostics, Troubleshooting & Disassembly | 15 | 14 | 1 |
| 6. Midea - Malfunction Codes | 11 | 11 | |
| 7. Midea - Components, Troubleshooting & Disassembly | 8 | 8 | |
| 8. Conversation History & Follow-ups | 8 | 7 | 1 |
| **Total** | **90** | | |

---

## Failed Test Analysis

### 5.3

The correct data was retrieved (page 2-12), but the LLM refused to answer. In the PDF, the Manual Overview Test Mode is a table where LOW SPIN and HIGH SPIN are separate rows - but both share the same LED code `8 1`. When extracted as flat text the row separation is lost, so the LLM sees two tests with identical LED codes and refuses rather than guessing.

Gentle Agitation (5.5) passed for comparison because its LED code `8 2 1` is unique in the table.

**Potential fix:** Render each table row as self-contained prose during PDF preprocessing to eliminate the ambiguity.

### 8.2 T3

The query "What are the next steps if that doesn't fix it?" is too vague for the query rewriter to reformulate into a specific retrieval query. Without a concrete subject, the rewritten query fails to surface the relevant chunk - which would describe checking PCB terminals and replacing the motor or PCB if damaged. The LLM refuses because nothing actionable is retrieved.

This is distinct from the 5.3 failure: here the data was never retrieved, not misread. The root cause is that heavily implicit follow-up questions strain the query rewriter when the conversation context spans multiple steps.

**Potential fix:** The query rewriter prompt could be strengthened to always produce a fully explicit query even from vague pronouns - e.g. resolving "if that doesn't fix it" into "next troubleshooting steps after checking motor terminals for E60 on Midea."