
# Design Document (v1.1)

## 1. Objectives & Context

### 1.1. Goal

Build an application that:

* Ingests **Women in Aviation International (WAI)** scholarship applications from a folder-based structure.
* Extracts and normalizes information from:

  * The **application form**.
  * Attachments (resumes, essays, recommendation letters, medical certificates, logbooks, etc.).
* Constructs multiple **profiles** per application (personal, academic, flight, etc.), each managed by its own **agent**.
* Each profile/agent can:

  * **Answer questions** about that profile.
  * **Summarize** its dimension of the candidate.
  * **Compute a score** for that dimension.
* An **Orchestrator** aggregates profile scores into:

  * A global **Application Score**.
  * A **ranked list** of applicants.
* Produces a **new “Review Worksheet Report”** (not tied to the old Excel sheet) for:

  * High-level monitoring by a scholarship manager.
  * Answering high-level questions.
  * Generating statistics and rankings.

### 1.2. WAI Context (Short)

Women in Aviation International (WAI):

* A global nonprofit supporting women in aviation and aerospace.
* Manages a significant scholarship program, with many applications per scholarship.
* Applications are heterogeneous: essays, recommendations, resumes, logbooks, medical certificates, etc.
* Review committees need **efficient, consistent, explainable** ranking and summarization.

---

## 2. Source Data & Folder Structure

Each **scholarship** (e.g., “Wings for Val Delaney Scholarship”) is represented by a folder that contains:

* A **process document** (e.g., a .docx describing how reviewers should work).
* An **applications folder** with **one folder per applicant**.

Each **application folder**:

* Is named after the **WAI membership number**, e.g. `75179/`.
* Contains:

  * **One application form PDF**, named like:

    * `75179_4.pdf`
      where:

      * `75179` = membership number
      * `4` = application number
    * This file has **no trailing “_N”** suffix.
  * **Multiple attachments**, named like:

    * `75179_4_1.pdf`
    * `75179_4_2.docx`
    * `75179_4_3.png`
    * Extension ∈ {`pdf`, `docx`, `png`} (can extend later).

**Naming regex** for files in the application folder:

```regex
^(\d+)_(\d+)(?:_(\d+))?\.(pdf|docx|png)$
```

* Group 1: `membership_number`
* Group 2: `application_number`
* Group 3: `attachment_index` (optional)
* Group 4: file extension

Semantics:

* `attachment_index == null` → **application form**.
* `attachment_index >= 1` → **attachment**.

---

## 3. Phase 1 Scope & Constraints

**Phase 1 intentional limitations:**

* **No OCR**:

  * Scanned PDFs and images (e.g., medical, logbook pages) will not yield text.
  * They are only **classified** and referenced, not parsed.
* Only **digital text extraction**:

  * `.docx` parsed via DOCX library.
  * `.pdf` parsed for digital text (if it exists).
* No requirement to align with the old Excel review worksheet:

  * We build our own **Review Worksheet Report** from scratch.
  * The old worksheet is historical reference only.

Future phases can add OCR + more sophisticated parsing.

---

## 4. Canonical Data Model (Core Entities)

This is the **evidence layer** that all agents and profiles draw from.

### 4.1. Scholarship

* `scholarship_id`
* `name`
* `year`
* `description`
* `process_doc_path`
* `applications_root_path`
* `created_at`
* `ingested_at`

---

### 4.2. Applicant

Person-level identity, shared across scholarships.

* `applicant_id`
* `wai_membership_number` (unique)
* `first_name`
* `middle_name`
* `last_name`
* `email`
* `membership_since`
* `membership_expiration`
* Home address fields (country, city, state/province, postal code, addresses, phones).
* Last known school info for this application:

  * `school_name`, `school_country`, `school_city`, etc.

---

### 4.3. Application

Specific submission to a scholarship.

* `application_id`
* `scholarship_id` (FK)
* `applicant_id` (FK)
* `wai_application_number`
* `application_form_path`
* `application_folder_path`
* `status` (`ingested`, `profiled`, `scored`, `shortlisted`, `winner`, etc.)
* `raw_form_metadata` (JSON snapshot of parsed form fields)

---

### 4.4. Attachment

Each file in the application folder (including the form as a special case).

* `attachment_id`
* `application_id` (FK)
* `original_file_name` (e.g. `75179_4_2.docx`)
* `file_path`
* `file_extension` (`pdf`, `docx`, `png`, …)
* `attachment_index` (null for application form; 1+ for attachments)
* `attachment_kind` (from LLM):

  * `application_form`
  * `resume`
  * `essay`
  * `recommendation_letter`
  * `medical_certificate`
  * `logbook`
  * `other`
* `kind_confidence` (0–1)
* `has_text` (bool)
* `text_extracted` (bool)
* `text_id` (FK to DocumentText, if any)

---

### 4.5. DocumentText

Text extracted from digital docs (no OCR).

* `text_id`
* `attachment_id` (FK)
* `content` (full text)
* `extraction_method` (`pdf_text`, `docx`)
* `extracted_at`

---

## 5. Profile Model & Agents

Instead of one big “application record,” we build **multiple profiles**, each handled by a custom **Profile Agent**.

### 5.1. Generic Profile Record

Every profile has a common shape:

* `profile_id`
* `application_id` (FK)
* `profile_type`
  (`application`, `personal`, `recommendation`, `academic`, `flight`, `medical`, `social_presence`)
* `summary_text` (narrative summary for humans)
* `score` (normalized; e.g., 0–100 or 1–10 mapped to 0–100)
* `score_breakdown_json` (profile-specific sub-scores, reasoning)
* `profile_features_json` (profile-specific structured features)
* `last_updated_at`
* `generated_by` (agent name, model version, etc.)

Each Profile Agent is responsible for populating these fields for its profile.

---

### 5.2. Individual Profiles

#### 5.2.1. Application Profile

**Purpose:** Overall snapshot of the application.

**Inputs:**

* Application form.
* Attachment inventory.

**Example fields in `profile_features_json`:**

* Identifiers:

  * `wai_membership_number`
  * `wai_application_number`
* Contact & school:

  * `name`, `email`, `school_name`, etc.
* Completeness:

  * `has_resume`
  * `has_essay`
  * `num_recommendation_letters`
  * `has_medical_certificate`
  * `has_logbook`
* Basic flags (e.g., suspiciously missing documents).

**ApplicationAgent responsibilities:**

* Summarize who this candidate is and what is in their package.
* Provide a simple **completeness/quality** score.

---

#### 5.2.2. Personal Profile

**Purpose:** Who the applicant is from inside the application – motivation, goals, character, community service, leadership.

**Inputs:**

* Essays and additional essays.
* Resume (especially objective, activities, leadership).
* Any narrative parts of the application form.

**Example fields:**

* `motivation_summary`
* `career_goals_summary`
* `aviation_path_stage` (exploring / training / early-career / professional)
* `community_service_summary`
* `leadership_roles`
* `personal_character_indicators` (e.g., persistence, teamwork – as tags)
* Scores:

  * `motivation_score`
  * `goals_clarity_score`
  * `character_service_leadership_score`
  * `overall_personal_profile_score`

**PersonalAgent responsibilities:**

* Summarize the applicant’s story, passion, and alignment with WAI and this scholarship.
* Provide sub-scores and an overall personal profile score.

---

#### 5.2.3. Recommendation Profile

**Purpose:** Capture what recommenders say.

**Inputs:**

* All attachments classified as `recommendation_letter`.

**Example fields:**

Per letter:

* `recommender_role` (instructor, employer, mentor, etc.)
* `relationship_duration`
* `key_strengths_mentioned`
* `potential_concerns`

Aggregate:

* `average_support_strength_score`
* `consistency_of_support_score`
* `overall_recommendation_profile_score`

**RecommendationAgent responsibilities:**

* Summarize endorsement themes and depth of support.
* Score recommendation strength and consistency.

---

#### 5.2.4. Academic Profile

**Purpose:** Academic readiness and rigor.

**Inputs:**

* Application form: school & program.
* Resume: education section.
* Academic attachments if any (transcripts, grade summaries – Phase 1 uses only text, no OCR).

**Example fields:**

* `current_school_name`
* `program`
* `education_level`
* `academic_awards`
* `relevant_courses`
* `academic_profile_score`

**AcademicAgent responsibilities:**

* Summarize academic trajectory and relevance.
* Provide academic readiness score.

---

#### 5.2.5. Flight Profile

**Purpose:** Flight training and experience.

**Phase 1 inputs:**

* Attachments classified as `logbook` (presence, count).
* Resume & essays (mentions of hours, ratings, training).

**Phase 1 fields:**

* `logbook_provided` (bool)
* `num_logbook_attachments`
* `flight_experience_summary` (text from resume/essay)
* `apparent_flight_stage` (e.g., “no flight yet”, “student pilot”, “licensed pilot” – inferred)
* `flight_profile_score` (qualitative, narrative-based)

**FlightAgent responsibilities:**

* Summarize flight-related experience from text.
* Provide a coarse flight profile score (no numeric hours yet).

---

#### 5.2.6. Medical Profile

**Purpose:** Medical documentation presence and basic reliability.

**Phase 1 inputs:**

* Attachments classified as `medical_certificate`.

**Phase 1 fields:**

* `medical_certificate_present` (bool)
* `num_medical_attachments`
* `medical_profile_score` (simple presence/completeness indicator)

**MedicalAgent responsibilities:**

* Indicate whether a medical certificate is present.
* Provide a simple score (e.g. 0 if missing, 1 if present; scaled to 0–10 or 0–100).

*(Future: DOB/height/weight via OCR + human validation.)*

---

#### 5.2.7. Social Presence Profile

**Purpose:** External digital presence (LinkedIn, Instagram, etc.) for **professionalism and aviation engagement**, not surveillance.

**Inputs:**

* Social links explicitly provided by the applicant:

  * In resume.
  * In application form fields (if any).
* (Optional) Verified handles / URLs if applicant opts in.

**Example fields:**

Per platform:

* `platform` (linkedin, instagram, facebook, tiktok, website, etc.)
* `url`
* `profile_type` (professional/personal/mixed – inferred)
* `aviation_content_presence` (none/low/medium/high)
* `professionalism_indicators` (tags)
* `obvious_red_flags` (none / potential / flagged – for human review)

Aggregate:

* `aviation_social_presence_score`
* `professionalism_score`
* `overall_social_presence_profile_score`

**SocialPresenceAgent responsibilities:**

* Summarize positive professional and aviation-related presence.
* Surface obvious positives (e.g., active chapter leader) and potential concerns for human review.
* Provide an overall social presence score, used as a small part of overall scoring.

---

## 6. Attachment Processing & Classification (Phase 1)

### 6.1. Identify Application Form

Per application folder:

1. List files matching the regex.
2. Find the file where `attachment_index == null`:

   * This is the **application form** (e.g., `75179_4.pdf`).
3. All files with `attachment_index >= 1` are attachments.

---

### 6.2. Parse the Application Form

* Extract fields from the form PDF:

  * WAI membership number, member since/expiration.
  * Name, email.
  * Home address & phone(s).
  * School information.
* Store into:

  * `Applicant` and `Application`.
  * Application Profile’s initial features.

---

### 6.3. Extract Text (No OCR)

For each attachment:

* `.docx` → parse text.
* `.pdf` → extract digital text (no OCR).
* `.png` (and images) → no text extracted in Phase 1.

Set:

* `has_text` and create a `DocumentText` if text exists.

---

### 6.4. LLM-based Attachment Type Classification

For each non-form attachment:

Inputs to LLM:

* `file_name`
* `file_extension`
* `text_excerpt` (first N chars if available)
* Context explaining that this is part of a WAI scholarship application and the possible types.

LLM outputs:

* `kind ∈ {resume, essay, recommendation_letter, medical_certificate, logbook, other}`
* `confidence` (0–1)
* `reason` (short explanation)

Persist to `attachment_kind` and `kind_confidence`.

---

## 7. Scoring & Orchestration

### 7.1. ScoringRubric

Each scholarship can define weights for profiles, for example:

* Personal Profile – 30%
* Recommendation Profile – 25%
* Academic Profile – 20%
* Flight Profile – 15%
* Medical Profile – 5%
* Social Presence Profile – 5%

We can store this in a `ScoringRubric` entity:

* `rubric_id`
* `scholarship_id`
* Per-profile weights (in JSON or a child table).

### 7.2. Orchestrator Flow

For each application:

1. **Run Profile Agents**:

   * ApplicationAgent
   * PersonalAgent
   * RecommendationAgent
   * AcademicAgent
   * FlightAgent
   * MedicalAgent
   * SocialPresenceAgent
2. Each agent:

   * Reads canonical data (Application, Attachments, DocumentText).
   * Produces: `summary_text`, `score`, `score_breakdown_json`, `profile_features_json`.
3. Orchestrator:

   * Normalizes scores.
   * Multiplies by rubric weights.
   * Computes `overall_application_score`.
   * Assigns a **rank** among all applications for that scholarship.

---

## 8. New Review Worksheet Report (Manager View)

We replace the legacy Excel review worksheet with our own **Review Worksheet Report** generated from the system.

### 8.1. Purpose

* Give the **scholarship manager** a high-level, interactive view of:

  * All applications.
  * Their profile scores and overall scores.
  * Completion status (profiles, data).
* Support:

  * Statistics and analytics.
  * Answering high-level questions from users/donors.
  * Exporting summaries and rankings.

### 8.2. Report Structure (Conceptual)

For a given scholarship:

**1. Summary section**

* Total number of applications.
* Distribution of overall scores (histogram or buckets).
* Average scores per profile (personal, recommendation, academic, flight, etc.).
* Number of candidates with:

  * Medical certificate present.
  * Logbooks present.
  * Social presence links present.

**2. Tabular “Review Worksheet” view**

One row per application, with columns like:

* Applicant:

  * Name
  * WAI membership #
* Overall:

  * `overall_application_score`
  * Rank
* Profiles (per dimension):

  * `personal_profile_score`
  * `recommendation_profile_score`
  * `academic_profile_score`
  * `flight_profile_score`
  * `medical_profile_score`
  * `social_presence_profile_score`
* Completeness flags:

  * `has_resume`, `has_essay`, `num_recommendation_letters`, etc.
* Links:

  * “View single-page summary.”
  * “Open original folder/files.”

This is your **new “review worksheet”**, generated from the system, not from Excel.

### 8.3. High-Level Questions the Manager Can Ask

Examples the system should answer easily:

* “Show me the top 10 applicants by overall score.”
* “How many applicants have no medical certificate on file?”
* “What is the average personal profile score vs academic profile score for this scholarship?”
* “Show applicants with strong recommendations (score ≥ 8) but moderate flight profile (≤ 6).”
* “How many applicants mention community service in their personal profile?”

These queries can be:

* Implemented via a **UI with filters & charts**, and/or
* Exposed to an LLM-based **manager assistant** that translates questions into queries against the data.

### 8.4. Outputs & Exports

* Export the Review Worksheet Report as:

  * CSV / Excel.
  * PDF summary per scholarship (for meetings).
* Export **single-page applicant summaries** as PDFs for the review committee.

---

## 9. Roadmap (Beyond Phase 1)

* **Phase 2**:

  * Add OCR for:

    * Medical certificates → DOB, height, weight, medical class (with human verification).
    * Logbooks → total hours, recent hours, aircraft categories.
  * Enhance Flight and Medical Profiles with structured data.
* **Phase 3**:

  * More sophisticated Social Presence analysis (still opt-in, transparent, and ethical).
  * Longitudinal tracking of applicants across multiple years/scholarships.
  * Advanced analytics dashboards (e.g., stats by region, training path, school).