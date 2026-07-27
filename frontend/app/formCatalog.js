/*
 * Static navigation metadata for the sidebar: which IPO forms exist, and
 * their official names. This is NOT a form definition and contains no
 * field/section/layout information — it only drives the sidebar list and
 * search, exactly as requested ("Form Number" / "Official Name").
 *
 * Names are copied verbatim from the verified index in
 * docs/specifications/README.md (each name was transcribed from the actual
 * government PDF during the specification phase — not re-derived here).
 *
 * formId matches the file-naming convention used by
 * docs/specifications/definitions/<formId>.definition.json. As of V1 only
 * form_03 has a definition file; the rest resolve to a graceful
 * "not yet available" state in the main area (see formLoader.js /
 * mainArea.js) rather than being invented.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var FORMS = [
    { formId: "form_01", formNumber: "1", officialName: "Application for Grant of Patent" },
    { formId: "form_02", formNumber: "2", officialName: "Provisional / Complete Specification" },
    { formId: "form_03", formNumber: "3", officialName: "Statement and Undertaking Under Section 8" },
    { formId: "form_04", formNumber: "4", officialName: "Request for Extension of Time or Condonation of Delay" },
    { formId: "form_05", formNumber: "5", officialName: "Declaration as to Inventorship" },
    { formId: "form_06", formNumber: "6", officialName: "Claim or Request Regarding Any Change in Applicant for Patent" },
    { formId: "form_07", formNumber: "7", officialName: "Notice of Opposition" },
    { formId: "form_07a", formNumber: "7A", officialName: "Representation for Opposition to Grant of Patent" },
    { formId: "form_08", formNumber: "8", officialName: "Request or Claim Regarding Mention of Inventor as Such in a Patent" },
    { formId: "form_08a", formNumber: "8A", officialName: "Certificate of Inventorship" },
    { formId: "form_09", formNumber: "9", officialName: "Request for Publication" },
    { formId: "form_10", formNumber: "10", officialName: "Application for Amendment of Patent" },
    { formId: "form_11", formNumber: "11", officialName: "Application for Direction of the Controller" },
    { formId: "form_12", formNumber: "12", officialName: "Request for Grant of Patent Under Section 26(1) & 52(2)" },
    { formId: "form_13", formNumber: "13", officialName: "Application for Amendment of the Application for Patent / Complete Specification / Any Document Related Thereto" },
    { formId: "form_14", formNumber: "14", officialName: "Notice of Opposition to Amendment / Restoration / Surrender / Compulsory Licence / Revision / Correction of Clerical Errors" },
    { formId: "form_15", formNumber: "15", officialName: "Application for the Restoration of Patent" },
    { formId: "form_16", formNumber: "16", officialName: "Application for Registration of Title/Interest in a Patent (or Share/Document Affecting Proprietorship)" },
    { formId: "form_17", formNumber: "17", officialName: "Application for Compulsory Licence" },
    { formId: "form_18", formNumber: "18", officialName: "Request / Express Request for Examination of Application for Patent" },
    { formId: "form_18a", formNumber: "18A", officialName: "Request for Expedited Examination of Application for Patent" },
    { formId: "form_19", formNumber: "19", officialName: "Application for Revocation of a Patent for Non Working" },
    { formId: "form_20", formNumber: "20", officialName: "Application for Revision of Terms and Conditions of Licence" },
    { formId: "form_21", formNumber: "21", officialName: "Request for Termination of Compulsory Licence" },
    { formId: "form_22", formNumber: "22", officialName: "Application for Registration of Patent Agent" },
    { formId: "form_23", formNumber: "23", officialName: "Application for the Restoration of the Name in the Register of Patent Agents" },
    { formId: "form_24", formNumber: "24", officialName: "Application for Review / Setting Aside Controller's Decision / Order" },
    { formId: "form_25", formNumber: "25", officialName: "Request for Permission for Making Patent Application Outside India" },
    { formId: "form_26", formNumber: "26", officialName: "Form for Authorisation of a Patent Agent / or Any Person in a Matter or Proceeding" },
    { formId: "form_27", formNumber: "27", officialName: "Statement Regarding the Working of Patented Invention(s) on a Commercial Scale in India" },
    { formId: "form_28", formNumber: "28", officialName: "To Be Submitted by a Small Entity / Startup / Educational Institution" },
    { formId: "form_29", formNumber: "29", officialName: "Request for Withdrawal of the Application for Patent" },
    { formId: "form_30", formNumber: "30", officialName: "To Be Used When No Other Form Is Prescribed" },
    { formId: "form_31", formNumber: "31", officialName: "Grace Period" }
  ];

  ns.formCatalog = { FORMS: FORMS };
})(window.PatentFormsApp);
