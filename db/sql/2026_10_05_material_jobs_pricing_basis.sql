-- A combined cut-and-edge invoice line identifies a supplied material detail,
-- not a universal per-piece operation price. Keep historical and new offers
-- explicitly supplier-defined until a source proves a reusable basis.
update public.company_supplier_operation_offers as offer
set pricing_basis = 'supplier_defined'
from public.reference_operations as operation
where offer.operation_id = operation.operation_id
  and operation.operation_code = 'supplier_cut_and_edge_banding'
  and offer.pricing_basis <> 'supplier_defined';
