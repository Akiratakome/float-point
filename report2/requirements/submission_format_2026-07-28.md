# Report 2 format and submission requirements

This is the current operational interpretation of the course-administration
email supplied on 2026-07-28 and the 2025--26 Course Handbook, pp. 11--12. It
supplements the project brief; if a later official notice conflicts with this
file, the later notice wins.

Official handbook:
`https://mphil.csc.cam.ac.uk/wp-content/uploads/2025/10/SciComp_Mphil_Handbook-2025-26.pdf`

## Document relationship and final PDF

- Report 1 and Report 2 are Part I and Part II of one Master's Dissertation.
- Report 2 remains a connected continuation and normally contains refinement
  of project direction, code verification/validation, results,
  post-processing, analysis, discussion, conclusions, and references.
- The final Report 2 submission PDF must contain the already submitted Report 1
  followed by Report 2.
- The point at which Report 2 begins must be unmistakable. The combined build
  therefore inserts a dedicated `PART II -- REPORT 2 STARTS HERE` divider.
- Report 1 may be corrected after feedback or research developments, but it is
  not marked again. Any change to it must be deliberate and separately logged.
- Report 2 should also remain an independent Overleaf project and be shared
  with `srs53@cam.ac.uk`, so the new material can be checked and counted without
  Report 1 contaminating its word count.

## Word count

- Formal maximum for Report 2: **7,500 words**, using the current Overleaf
  count for the Report 2 project only.
- Included: tables, figure legends/captions, and appendices.
- Excluded: bibliography.
- Internal target: at most 7,200 words, leaving integration margin.
- The tolerance bands are not writing targets:
  - up to 7,875 words: no deduction;
  - 7,876--8,250: 10 percentage-point deduction from Quality of Work;
  - 8,251--9,000: 20 percentage-point deduction;
  - 9,001 or more: resubmission within 48 hours, or the applicable penalty.

Record the final Overleaf count and its date in the release checklist. Do not
use a combined Report 1 + Report 2 count as the Report 2 declaration.

## Page format and declarations

- Use 12-point type, one-and-a-half or double spacing, A4, and margins of at
  least 2 cm.
- The originality declaration must follow the title page of each report. The
  current Report 2 declaration contains the wording specified by the handbook.
- A completed Certificate of Submission, signed anti-plagiarism declaration,
  and word-count declaration are required. The administration email permits
  the signed Report 2 declaration as a separate file or inside the Report 2
  PDF.
- The attached official declaration form is not present in this repository.
  Do not fabricate a signature. Obtain, complete, sign, and include or submit
  that form before release.

## Required submission artefacts

1. Standalone Report 2 PDF used for Overleaf word counting and supervisor
   sharing.
2. Combined PDF containing Report 1, an explicit Part II divider, and Report 2.
3. Signed Report 2 declaration/cover sheet, separately or embedded.
4. Word-count declaration for Report 2 only.
5. LaTeX sources, input/config files, analysis procedures, plotting scripts,
   and personally written project source code needed to reproduce the report.

The combined-PDF workflow is documented under `report2/submission/`. PDF
merging is a presentation step; it must not duplicate Report 1 text inside the
Report 2 word count or merge the two source trees into one label/bibliography
namespace.
