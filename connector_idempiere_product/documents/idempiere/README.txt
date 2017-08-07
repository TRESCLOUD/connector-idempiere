Register of Web Service in iDempiere
=====================================

Description
-----------

The Web Services must be published by iDempiere in order to be consumed.

Steps
--------

1) Run 2Pack to Create "product_product" view:

- Login to iDempiere with a user with access to Client: System.
- Open the "Pack In" window.
- New record and enter a name for the record eg "Create product_product view".
- Attach the 2Pack located in "Custom addons path"/conector_idempiere_product/documents/idempiere/2Pack_ProductView.zip using the "Attachment" button
- Click the "PackIn" button
- Confirm with the "OK" button.

2) Import Web Services Type

- Login to iDempiere with a Business Group user with read-write access to the "Web Service Security" window.
- Open the "Web Service Security" window and click the "Import File Loader" button at the toolbar..
- Select "Import Mode: Insert".
- Select File to Load : "Custom addons path"/conector_idempiere_product/documents/idempiere/WebServiceType_Product.csv
- Confirm with the "OK" button.
- In each inserted WebService, register the roles that will have access to the webservice in the tab "Web Service Access":
    Web Service Inserted:
    - QueryProductTest
    - QueryProduct

3) Run 2Pack to update Web Service parameters that can not be changed through the window of the previous step.

- Login to iDempiere with a user with access to Client: System.
- Open the "Pack In" window.
- New record and enter a name for the record eg "Update QueryProduct Parameter".
- Attach the 2Pack located in "Custom addons path"/conector_idempiere_product/documents/idempiere/2Pack_UpdateQueryProductPARA.zip using the "Attachment" button
- Click the "PackIn" button
- Confirm with the "OK" button.