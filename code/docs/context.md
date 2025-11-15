# **1. Context Information: Women in Aviation International & Scholarship Review**

## **1.1. About Women in Aviation International (WAI)**

Women in Aviation International (WAI) is a global nonprofit organization dedicated to advancing women in all aviation and aerospace career fields. WAI supports its members through:

* Professional development and mentorship
* Networking events
* STEM outreach
* Annual conferences
* Substantial financial support through scholarships

Each year, WAI awards **hundreds of thousands of dollars** in scholarships to support women pursuing:

* Fixed-wing pilot training
* Rotorcraft/helicopter ratings
* Drone/UAS certifications
* Aircraft maintenance
* Aerospace engineering
* Air traffic control
* Aviation academics and research
* And many other aviation disciplines

The WAI scholarship program is one of the **largest and most diverse aviation education funding programs in the United States**.

---

## **1.2. How WAI Scholarships Work**

Each **scholarship** (e.g., *Wings for Val Delaney Scholarship*) has:

* A sponsoring donor (individual, foundation, corporate, or memorial fund)
* A scholarship description defining:

  * Purpose
  * Target applicant profile
  * Eligibility requirements
  * Award amount
  * Number of recipients
* A structured application package that all applicants must submit
* A review committee that selects the recipients

A scholarship typically receives anywhere from **dozens to hundreds** of applications.
Review committees often consist of:

* Donors or representatives
* Aviation professionals
* WAI leadership or staff
* Volunteers familiar with the aviation domain

Each committee must identify:

1. **Strongest candidates**
2. **Most suitable according to criteria**
3. **At least one runner-up**
4. **Final recipient(s)**

All final decisions must be reported to WAI staff (e.g., Donna, Annie) by a specific deadline so that award letters can be issued.

---

## **1.3. Nature of Scholarship Applications**

Each application is submitted digitally through the WAI system and exported into:

* A **scholarship folder**, containing:

  * A **review worksheet Excel file** listing all applicants
  * A folder of **individual applicant subfolders**

Each **applicant folder** is named by their **WAI Membership Number**, e.g.:

```
75179/
    75179_4.pdf          # Application form
    75179_4_1.pdf        # Attachment 1
    75179_4_2.docx       # Attachment 2
    75179_4_3.png        # Attachment 3
    ...
```

The **application form** contains structured profile information:

* Name
* Contact information
* WAI membership status
* Address
* Education/school info
* Essay references
* Recommendation references

The **attachments** may include:

* Recommendation letters
* Essays
* Resumes
* Medical certificates (often scanned forms)
* Logbook pages (PDFs or images)
* Other documents supporting the applicant’s aviation journey

Attachment formats can vary widely (`pdf`, `docx`, `png`, `jpg`), and some contain only scanned images (no extractable text).

---

## **1.4. Problems Faced by Reviewers Today**

Manual reviewing is:

* **Time-consuming**

  * Reviewers open each attachment individually.
  * They manually sort through essays, recommendation letters, certificates, and logbooks.

* **Unstandardized**

  * Documents are inconsistent in naming and structure.
  * Some are poorly scanned, hard to read, and cannot be text-searched.

* **Repetitive**

  * Reviewers must re-extract basic information (flight hours, DOB, school data).

* **Difficult to rank objectively**

  * Reviewers must manually assign scores and totals via an Excel sheet.
  * The rubric is in a separate tab and easy to overlook.

WAI review committees often work under tight deadlines (e.g., results due December 5), making efficient review even more critical.

---

## **1.5. Why Build an Automated Scholarship Reviewer Application**

The purpose of the “Scholarship Reviewer Application” is to support reviewers by:

### **1.5.1. Normalizing and analyzing each application**

The system should:

* Ingest the scholarship folder
* Automatically detect the application form
* Extract structured information about the applicant
* Categorize attachments (resume, recommendation, medical, logbook, etc.)
* Prepare summaries from essays and recommendation letters

### **1.5.2. Supporting manual scoring and ranking**

The review worksheet contains:

* Applicant list
* Reviewer-defined scoring criteria (1–10 per criteria)
* Total score formulas
* Reviewer notes fields

Your system should map this structure into a digital scoring system where:

* Criteria are clear
* Scores are consistent
* Rankings are automatic
* Reviewers can still manually override or comment

### **1.5.3. Improving reviewer efficiency**

The end goal is to provide:

* A **single-page summary** for each applicant
* Automatic attachment classification
* Optional LLM-generated summaries or insights
* Clean scoring and ranking interface
* Ability to instantly retrieve medical certificates, resumes, essays, and logbooks

This helps reviewers:

* Compare applicants faster
* Make more evidence-based decisions
* Stay aligned with WAI’s rubric
* Focus on quality rather than document management

### **1.5.4. Reducing human error**

By standardizing extraction, classification, scoring, and ranking:

* Fewer applicants are misfiled or overlooked
* Scores are consistent across reviewers
* Form data is not incorrectly transcribed
* Submission deadlines are easier to meet

---

## **1.6. What This System Will *Not* Do (Phase 1)**

To keep the design realistic:

* **No OCR** (in Phase 1)
  Medical certificates and logbooks will not be machine-parsed—just classified.

* **No automated eligibility rejection**
  Reviewers remain the authority.

* **No inference on aviation qualifications** beyond what is extractable from text-rich documents.

These may be added in Phase 2–3.

---

## **1.7. Summary of the Context**

Your “Scholarship Reviewer Application” exists to:

* Support WAI reviewers reviewing scholarship applications
* Automate data ingestion, structuring, and classification
* Help produce ranked applicant lists
* Generate single-page candidate summaries
* Improve consistency, speed, and accuracy
* Preserve reviewer control and judgment
