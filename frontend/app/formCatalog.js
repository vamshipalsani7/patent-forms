/*
 * Static navigation metadata for the sidebar: which IPO forms exist, the action
 * each one performs, and their official names.
 *
 * `action` is the action-first label the sidebar leads with — a patent
 * professional thinks "I need to request expedited examination", not "I need
 * Form 18A". The form number is shown as secondary confirmation. `officialName`
 * is the verbatim government title, kept for search and reference.
 *
 * This is NOT a form definition and contains no field/section/layout
 * information. formId matches docs/specifications/definitions/<formId>.definition.json;
 * every form has a definition (all 34 authored), so selecting any of them opens
 * a real pre-fillable form.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var FORMS = [
    { formId: "form_01", formNumber: "1", action: "File a Patent Application", officialName: "Application for Grant of Patent" },
    { formId: "form_02", formNumber: "2", action: "Submit a Specification", officialName: "Provisional / Complete Specification" },
    { formId: "form_03", formNumber: "3", action: "Declare Foreign Applications (Section 8)", officialName: "Statement and Undertaking Under Section 8" },
    { formId: "form_04", formNumber: "4", action: "Request an Extension of Time", officialName: "Request for Extension of Time or Condonation of Delay" },
    { formId: "form_05", formNumber: "5", action: "Declare Inventorship", officialName: "Declaration as to Inventorship" },
    { formId: "form_06", formNumber: "6", action: "Record a Change of Applicant", officialName: "Claim or Request Regarding Any Change in Applicant for Patent" },
    { formId: "form_07", formNumber: "7", action: "File a Notice of Opposition", officialName: "Notice of Opposition" },
    { formId: "form_07a", formNumber: "7A", action: "File a Pre-Grant Opposition", officialName: "Representation for Opposition to Grant of Patent" },
    { formId: "form_08", formNumber: "8", action: "Request Mention as Inventor", officialName: "Request or Claim Regarding Mention of Inventor as Such in a Patent" },
    { formId: "form_08a", formNumber: "8A", action: "Request a Certificate of Inventorship", officialName: "Certificate of Inventorship" },
    { formId: "form_09", formNumber: "9", action: "Request Early Publication", officialName: "Request for Publication" },
    { formId: "form_10", formNumber: "10", action: "Apply to Amend the Patent", officialName: "Application for Amendment of Patent" },
    { formId: "form_11", formNumber: "11", action: "Request a Direction of the Controller", officialName: "Application for Direction of the Controller" },
    { formId: "form_12", formNumber: "12", action: "Request Grant (Sections 26 & 52)", officialName: "Request for Grant of Patent Under Section 26(1) & 52(2)" },
    { formId: "form_13", formNumber: "13", action: "Amend the Application or Specification", officialName: "Application for Amendment of the Application for Patent / Complete Specification / Any Document Related Thereto" },
    { formId: "form_14", formNumber: "14", action: "Oppose an Amendment or Restoration", officialName: "Notice of Opposition to Amendment / Restoration / Surrender / Compulsory Licence / Revision / Correction of Clerical Errors" },
    { formId: "form_15", formNumber: "15", action: "Restore a Lapsed Patent", officialName: "Application for the Restoration of Patent" },
    { formId: "form_16", formNumber: "16", action: "Register a Title or Assignment", officialName: "Application for Registration of Title/Interest in a Patent (or Share/Document Affecting Proprietorship)" },
    { formId: "form_17", formNumber: "17", action: "Apply for a Compulsory Licence", officialName: "Application for Compulsory Licence" },
    { formId: "form_18", formNumber: "18", action: "Request Examination", officialName: "Request / Express Request for Examination of Application for Patent" },
    { formId: "form_18a", formNumber: "18A", action: "Request Expedited Examination", officialName: "Request for Expedited Examination of Application for Patent" },
    { formId: "form_19", formNumber: "19", action: "Apply to Revoke for Non-Working", officialName: "Application for Revocation of a Patent for Non Working" },
    { formId: "form_20", formNumber: "20", action: "Revise Licence Terms", officialName: "Application for Revision of Terms and Conditions of Licence" },
    { formId: "form_21", formNumber: "21", action: "Terminate a Compulsory Licence", officialName: "Request for Termination of Compulsory Licence" },
    { formId: "form_22", formNumber: "22", action: "Register as a Patent Agent", officialName: "Application for Registration of Patent Agent" },
    { formId: "form_23", formNumber: "23", action: "Restore Patent Agent Registration", officialName: "Application for the Restoration of the Name in the Register of Patent Agents" },
    { formId: "form_24", formNumber: "24", action: "Request Review of a Controller's Order", officialName: "Application for Review / Setting Aside Controller's Decision / Order" },
    { formId: "form_25", formNumber: "25", action: "Request Permission to File Abroad", officialName: "Request for Permission for Making Patent Application Outside India" },
    { formId: "form_26", formNumber: "26", action: "Authorise a Patent Agent", officialName: "Form for Authorisation of a Patent Agent / or Any Person in a Matter or Proceeding" },
    { formId: "form_27", formNumber: "27", action: "File a Statement of Working", officialName: "Statement Regarding the Working of Patented Invention(s) on a Commercial Scale in India" },
    { formId: "form_28", formNumber: "28", action: "Claim Small Entity or Startup Status", officialName: "To Be Submitted by a Small Entity / Startup / Educational Institution" },
    { formId: "form_29", formNumber: "29", action: "Withdraw the Application", officialName: "Request for Withdrawal of the Application for Patent" },
    { formId: "form_30", formNumber: "30", action: "Make a General Request", officialName: "To Be Used When No Other Form Is Prescribed" },
    { formId: "form_31", formNumber: "31", action: "Claim the Grace Period", officialName: "Grace Period" }
  ];

  ns.formCatalog = { FORMS: FORMS };
})(window.PatentFormsApp);
