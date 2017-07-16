Register of Web Service in iDempiere
=====================================
Note: tested with version iDempiere 2.1


Description
-----------

The Web Services must be published by iDempiere in order to be consumed.

Steps
--------

1) Import Web Services Type

- Login to iDempiere with a Business Group user with read-write access to the "Web Service Security" window.
- Open the "Web Service Security" window and click the "Import File Loader" button at the toolbar.
- Select "Import Mode: Insert".
- Select File to Load : "Custom addons path"/conector_idempiere_salesorder/documents/idempiere/WebServiceType_SalesOrder.csv
- Confirm with the "OK" button.
- In each inserted WebService, register the roles that will have access to the webservice in the tab "Web Service Access"
    Web Service Inserted:
    - CreateOrderTest
    - CreateOrderLineTest
    - DocActionOrderTest
    - CompositeOrderTest

