# Documentation for the script LIB_AP_CUSTOMIZATION_COMMON_SAMPLE.js #

This guide organizes the 80+ hooks into their specific "Districts" (Namespaces).

## 1. 🏠 The Common District (General Settings)##
These hooks affect the general behavior of the invoice form, independent of the specific ERP or Workflow.

Hook Name,What it does
CustomUserExits,Defines custom functions accessible outside the library.
CustomFunctions,Defines business functions (not user exits) for server/client.
GetCustomFilterForPODateUpdate,Changes how the system finds the last PO event date.
GetVendorCustomFields,Adds custom fields to the Vendor search and form.
GetRequiredFields,(Core) Defines which fields are mandatory before submission.
GetCodingsPredictionFields,"lists fields used by the AI to predict coding (GL, Cost Center)."
OnInitInternalConversationPane,"Customizes the chat window settings (e.g., disabling confirmation)."
OnGetCodingsPredictionResults,Modifies the AI prediction results before they are applied.
OnItemFieldSetConfidence...,Customizes what happens when AI sets a confidence score on a field.
EnableCodingsPrediction,Turns the AI coding prediction ON or OFF based on conditions.
EnableCodingsTemplates,Turns the Coding Templates feature ON or OFF.
SetAlertWhenExtractedIBAN...,Changes the warning level when the IBAN on the invoice doesn't match master data.
OnValidateForm,(Core) Validates data when the user clicks Post/Submit. Returns false to stop.
FillCostType,"(Core) Automatically sets ""CapEx"" or ""OpEx"" based on the G/L Account."
CustomizeCurrenciesPrecision,"Changes decimal precision for specific currencies (e.g., HUF, JPY)."
GetTaxRoundingParameters,"Changes how taxes are rounded (e.g., round half-up vs. round down)."
CustomizeMultipleTaxesSeparator,Changes the symbol used to separate multiple tax codes (default is ;).
SetInvoiceUseMultipleTaxes,Enables or disables selecting multiple tax codes for a single line.
CustomizeTaxRateQueryFilter,Filters which Tax Rates are visible to the user.
CustomizeAutomaticMessage,Changes the text of auto-generated messages in the conversation.
AllowEditingDiscountAmount,Decides if the user can manually change the Discount Amount field.
DeactivateLocalPOTableUpdates,Prevents the system from updating local PO tables (advanced usage).
getDefaultParametersValues,Sets defaults for duplicate check level and touchless settings.
IsDynamicDiscountingAllowed,Enables or disables the Dynamic Discounting feature.
OnComputeBackdatingTargetDate,Customizes the calculation of the posting date for backdating.
OnComputeDueDate,Customizes how the Invoice Due Date is calculated.
OnInvoiceStatusChange,"Runs custom logic before the status changes (e.g., to ""Paid"")."
OnInvoiceStatusChangeFromExternal...,Runs logic when status is updated by an external system.
GetDefaultIntercompanyInvoice...,Customizes the ID used for archiving intercompany invoices.
GetClearableFields,Lists fields to clear before Touchless archiving.
IsInternationalVATNumber,"Custom logic to decide if a VAT number is ""International""."
OnLoadTemplateLine,Customizes a specific line item when a Template is loaded.
OnLoadTemplateEnd,Runs logic after a Template has finished loading.
CustomizeLoadTemplateQueryOptions,Filters which templates are shown to the user.
OnReprocessInitiated,Saves variables to be used when the invoice is re-extracted.
OnComputeHeaderAmount,(Core) Customizes how the total Net Amount is summed up.
OnComputeItemMismatchAmount,Customizes how the Mismatch Amount is calculated for a line.
CalculateCustomBalance,Adds custom logic to the Balance equation (Invoice - Net - Tax).
ActivateEmailNotificationOn...,Turns on email alerts when a payment proposal is approved.
ShouldSkipCalculateTax,Skips the tax calculation step for specific lines.
OnComputeHeaderTaxAmount,Customizes how the total Tax Amount is summed up.
CustomPaymentTermsAttributes,Reads extra fields when fetching Payment Terms.
CustomizePaymentTermsQueryFilter,Filters which Payment Terms are available.
CustomAPMappingXMLParameters,Configures how XML files are read.
InvoiceToProcessFilterFor...,Filters which invoices are used for Workflow Prediction training.
DisableReloadConfiguration...,Stops the form from reloading config when Company Code changes.
HandleCompanyCodeChange,Runs custom logic immediately when Company Code is changed.
OverrideErrorsOnGetAndFill...,Suppresses standard errors on specific fields.
UseCustomAttributesToSelect...,Custom logic to pick the default Bank Details.
GetNbBankAccountsToRetrieve,Sets how many bank accounts to load (default is 50).
IsDocumentCreditNote,"Custom logic to define what counts as a ""Credit Note""."
CustomizeInvoiceStatementMatching...,Filters invoices used for Statement Matching.
IsLineVendorNumberValid,Validates if the line-item vendor matches the header vendor.
GetCustomLineItemCompanyCode,Sets a custom Company Code for a specific line item.
AllowAutoPostAfterReview,Allows the invoice to post automatically after a reviewer approves.
OverrideDownPaymentInvoiceSupport,Enables Down Payment support for specific ERPs.
KeepUnprocessedLineItems,Keeps extra PO lines on the form even if not matched.

## Now let us see some examples to how to implement the user exits/ hooks:##

### Topic 1: The Gatekeeper (Making Fields Required) ###
In your file, search for the function named GetRequiredFields (around line 124).

🚂 The Concept: Imagine the "Submit" button on your form is a gate. Usually, the gate opens easily. But sometimes, you want a guard there to say, "Stop! You cannot pass until you show me your Invoice Number."

This script is that guard. It tells the system which fields must be filled in before the user can continue.
*/

`Common.GetRequiredFields = function (requiredFields) {
	// Step 1: Tell the system that "InvoiceNumber__" is mandatory (true)
	requiredFields.Header.InvoiceNumber__ = true;

	// Step 2: Return the updated list of rules to the system
	return requiredFields;
};`

/* Example 2: What if you only want a field to be required IF something else is true?
(e.g., "If the Amount is huge, you must provide a Comment").
*/
`Common.GetRequiredFields = function (requiredFields) {
	// Logic: If the Line Type is "GL" (General Ledger), then the Account field is required.

	requiredFields.LineItems__.GLAccount__ = function(item) {
		// Get the value of the "LineType" for this specific row
		var type = item.GetValue("LineType__");

		// Return TRUE if type is 'GL'. Return FALSE otherwise.
		return (type === 'GL');
	};

	return requiredFields;
};`

### Topic 2: The Auto-Filler (Reading & Writing Data) ###
Now that you know how to make fields required, let's learn how to automatically fill them in.

🚂 The Concept: Imagine you are the conductor again.

Reading (GetValue): You look at a passenger's ticket to see their destination.

Writing (SetValue): Based on that destination, you stamp "Zone A" or "Zone B" on their ticket.

In your scripts, you will use two very important commands for this:

item.GetValue("FieldID__") = Read what is currently in a box.

item.SetValue("FieldID__", "New Value") = Write something new into a box.

The Hook: Common.FillCostType Search for this function in your file (around line 430).

Its job is to look at the G/L Account and automatically decide if the Cost Type is "OpEx" (Operating Expense) or "CapEx" (Capital Expense).

`Common.FillCostType = function (item) {
	// Step 1: Read the value of the G/L Account
	var account = item.GetValue("GLAccount__");

	// Step 2: Check the value (The Logic)
	if (account === "8300") {
		// Step 3: Write "CapEx" into the Cost Type field
		item.SetValue("CostType__", "CapEx");
	}
	else {
		// Step 4: Otherwise, write "OpEx"
		item.SetValue("CostType__", "OpEx");
	}
};`

### Topic 3: The Bouncer (Stopping the Process) ###
Sometimes, simply filling in a field isn't enough. You need to check if the data makes sense before the user finishes.

🚂 The Concept: Imagine a Bouncer at a club.

The Library: The club entrance.

The Hook (OnValidateForm): The moment the user tries to enter (clicks "Post").

Your Script: You decide if they get in (return true) or get turned away (return false).

The Hook: Common.OnValidateForm Search for this function in your file (around line 324).

Key Takeaways:
return false = Stop everything. The form will not submit.

return true = Everything looks good. Proceed.

*/

`Common.OnValidateForm = function (isFormValid) {

	// Step 1: Read the value (e.g., Invoice Date)
	var myDate = Data.GetValue("InvoiceDate__");

	// Step 2: The Logic (Check if the date is missing)
	if (!myDate) {
		// Step 3: Stop the process!
		// We also usually show an error message so they know why.
		Data.SetError("InvoiceDate__", "You must provide a date!");
		// eslint-disable-next-line line-comment-position
		return false; // <--- The Bouncer says NO.
	}

	// Step 4: If we made it here, let them in.
	return true; // <--- The Bouncer says YES.
};`

### Topic 4: The Inspector (Looping Through Lines) ###
There is one final "Big Boss" concept to learn. An invoice usually has a list of items (Line Items), like rows in a spreadsheet. Sometimes you need to check every single row.

🚂 The Concept: Imagine you are an inspector on a factory line. You don't just look at the box; you pick up every single item inside to make sure it's not broken.

The Loop: This is the conveyor belt moving the items past you.

The Item: The specific object you are holding right now.

The Hook: We often use a helper function to do this easily. In your file, you can see this pattern used in Common.OnComputeHeaderAmount.

Search for this function (around line 376).
*/

`// Function to check every line
function CheckEveryLine() {

	// Step 1: Start the conveyor belt (The Loop)
	// "LineItems__" is the name of the table we want to inspect.
	Sys.Helpers.Data.ForEachItem("LineItems__", function (item) {

		// Step 2: Inspect the current item
		// This code runs again and again for EVERY row in the table.
		var cost = item.GetValue("Amount__");

		if (cost > 100) {
			item.SetWarning("Amount__", "This is expensive!");
		}

	}); // End of the loop
}`

### Let's do a Mini-Challenge to make sure you have mastered the "Inspector".

### Scenario: We want to make sure no single line item has a huge quantity. You need to loop through the table and check if the Quantity (Quantity__) is greater than 50.###

Your Task: Can you write the code block to:

Loop through "LineItems__".

Read the Quantity__.

If it is greater than (>) 50, put an error on that field: item.SetError("Quantity__", "Too many!").

(Hint: Use Sys.Helpers.Data.ForEachItem to start).

`// Mini-Challenge Solution by Vijay R.S.
function CheckEveryLine() {
	// Step 1: Start the conveyor belt (The Loop)
	var invAmount = Data.GetValue("InvoiceAmount__");
	if (invAmount > 1000) {
		    Sys.Helpers.Data.ForEachItem("LineItems__", function (item) {

			// Step 2: Inspect the current item
			// This code runs again and again for EVERY row in the table.
			var costCentre = item.GetValue("CostCenter__");

			if (!costCentre) {
				item.SetError("CostCenter__","Cost Center Required for high amounts!");
			}

		});
	}
}`


## 🔀 The Workflow District: AutoGuessException
The Concept: Think of the AP system as having a built-in "Detective." 🕵️‍♀️

By default, when an invoice arrives, this Detective looks at the numbers. If the Invoice Amount doesn't match the Purchase Order Amount, the Detective automatically yells, "Price Mismatch Exception!" and blocks the invoice.

Sometimes, this Detective is too aggressive. You might want to silence them so the human AP Specialist can decide if it's a real problem or just a small variance.

The Hook: AutoGuessException is the switch to turn this Detective ON or OFF.
*/

Common.Workflow.AutoGuessException = function (action, computeControllers, computeApprovers) {

	// Logic: Do we want the system to auto-detect problems?

	// return true = YES (The Detective works automatically)
	// return false = NO (The Human must select exceptions manually)

	return false;
};


🔀 The Workflow District: AutoGuessException
The Concept: Think of the AP system as having a built-in "Detective." 🕵️‍♀️

By default, when an invoice arrives, this Detective looks at the numbers. If the Invoice Amount doesn't match the Purchase Order Amount, the Detective automatically yells, "Price Mismatch Exception!" and blocks the invoice.

Sometimes, this Detective is too aggressive. You might want to silence them so the human AP Specialist can decide if it's a real problem or just a small variance.

The Hook: AutoGuessException is the switch to turn this Detective ON or OFF.
*/

Common.Workflow.AutoGuessException = function (action, computeControllers, computeApprovers) {

	// Logic: Do we want the system to auto-detect problems?

	// return true = YES (The Detective works automatically)
	// return false = NO (The Human must select exceptions manually)

	return false;
};

## 2. 📦 The Purchase Order District
Hooks specific to handling POs and Goods Receipts.

Hook Name,What it does
AddPoLine,Decides if a PO line should be added to the invoice table.
OnAddPOLine,(Core) Customizes data on a PO line as it is being added.
GetExtendedPOSearchCriteria,"Allows searching for POs using complex logic (e.g., wildcards)."
ModifyOrderNumbersToSearch,Modifies the list of PO numbers before the database search.
SetErrorWhenPOVendorDiffers...,Sets an error if the PO Vendor doesn't match the Invoice Vendor.

## 3. 🇩🇪 The SAP District
Hooks that only run if your ERP is SAP.

Hook Name,What it does
GetBAPIName,"Overrides standard BAPI names with custom ""Z_"" BAPIs."
GetDefaultBAPIParams,Configures parameters sent to the BAPI.
SAPCurrenciesExternalFactors,"Fixes currency decimal issues in SAP (e.g., JPY, IDR)."
SAPCheckVendorNumber,Custom validation for SAP Vendor Numbers.
ShouldAddAccDataParameter...,Controls if accounting data is sent to the Tax BAPI.
GetAccDataParameterForTax...,Customizes the data sent to the Tax BAPI.
TrimPartNumberLeadingZeros,Removes zeros from the start of Part Numbers.
CustomQueryLanguage,"Forces SAP queries to use a specific language (e.g., ""EN"")."
CustomizeDocumentType,"Sets the SAP Document Type (e.g., ""KR"", ""RE"") based on logic."
IsEKBECacheEnabled,Turns caching ON/OFF for PO History queries.
CustomizeWSParams,Customizes SOAP Web Service headers.
CustomizeMMInvoiceDocument...,Filters the document type when looking up MM invoices.
CustomMultipleAccountAssignment...,Custom logic for handling multiple account assignments.
IsTaxJurisdictionError,Identifies if an SAP error is specifically about Tax Jurisdiction.
CustomizedTaxErrorMessage,Changes the error message for tax issues.
itemNumberIdx,Adjusts the item index number sent to SAP.
CustomizeExtendedWithholding...,Filters the Withholding Tax query.
GetWSCustomErrorMessage,Extracts a custom error message from an SAP Web Service response.
GetSAPToUTCOffsetInHours,Adjusts time zones between SAP and the Web Interface.
GetPOItemHistoryForCompute...,Selects which history item to use for GR calculations.
DisableUpdateOfOpenAndExpected...,"Stops the system from updating ""Open"" amounts during simulation."
VendorBankDetails_...,Adds custom fields to Bank/IBAN queries (Multiple hooks).
GetCustomFilterForTaxProcedure,Filters which Tax Procedures are used.
CustomizeLineItemExpectedValues,"Customizes what the system ""Expects"" (Amount/Qty) for a line."
ValidateFIGLLine,Custom validation for FI-GL lines.
SkipAddAccountAssignmentLine,"Skips adding account assignment lines (e.g., for Service Sheets)."
SkipReadAccountAssignment,Skips reading account assignment data from SAP.
GetBAPIPOGetDetailsConfig,Configures BAPI_PO_GETDETAIL to fetch extra data (Extensions).
GetCustomExchangeRateType,"Selects a specific Exchange Rate Type (e.g., ""M"" or ""B"")."
PlannedDeliveryCosts,(Namespace) Customizes delivery cost filters.
DuplicateCheck,(Namespace) Customizes how duplicates are found and reported.
Query,(Namespace) Advanced customization of specific SAP database queries.

## 4. 🔀 The Workflow District
Hooks that control the approval chain and exceptions.

Hook Name,What it does
OnBuildOfReviewers,Controls if Reviewers are re-calculated when data changes.
OnBuildOfApprovers,Controls if Approvers are re-calculated when data changes.
AutoGuessException,(Core) Auto-detects exceptions (Price/Qty mismatch). Return false to disable.
GetQuantityMismatchTolerance...,Sets a tolerance (Absolute or %) for Quantity mismatch.
GetUnitPriceMismatchTolerance...,Sets a tolerance (Absolute or %) for Price mismatch.
SetCustomInvoiceStatusAfterReview,"Decides the status (e.g., ""To Post"") after review is done."

5. 🌐 Generic ERP & EDI
Hooks for non-SAP ERPs and Electronic Data Interchange.

Hook Name,What it does
OverrideStoredInLocalTableFields,Changes which fields are saved to the local database.
BankDetailsCustomAttributes,Adds custom fields to Bank Details.
CustomizeExtendedWithHolding...,Filters the Withholding Tax table.
FillAdditionalLineFieldsFromMapper,Maps extra data from an EDI file to the invoice line.