CREATE OR REPLACE VIEW product_product AS
SELECT
p.Name as name,
p.Value as default_code,
pp.PriceList as list_price,
pc.Name as category_name,
COALESCE(( SELECT max(t.rate) AS rate
           FROM c_tax t
             JOIN m_product p_1 ON p_1.c_taxcategory_id = t.c_taxcategory_id
          WHERE t.isdefault = 'Y'::bpchar AND p_1.m_product_id = p.m_product_id AND t.SOPOType IN ('B','S')), ( SELECT max(t.rate) AS max
           FROM c_tax t
             JOIN m_product p_1 ON p_1.c_taxcategory_id = t.c_taxcategory_id
          WHERE p_1.m_product_id = p.m_product_id)) AS rate_taxe,
CASE p.producttype
	WHEN 'I'::bpchar THEN 'product'::text
        WHEN 'S'::bpchar THEN 'service'::text
        ELSE 'consu'::text
END AS type,
p.M_Product_ID,
p.AD_Client_ID,
p.AD_Org_ID,
p.IsActive,
p.CreatedBy,
p.Created,
p.UpdatedBy,
p.Updated
FROM M_Product p
JOIN M_ProductPrice pp ON (p.M_Product_ID = pp.M_Product_ID)
JOIN M_Product_Category pc ON (p.M_Product_Category_ID = pc.M_Product_Category_ID)
WHERE pp.M_PriceList_Version_ID = 101 AND p.AD_Client_ID = 11