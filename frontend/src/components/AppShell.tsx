import { Routes, Route, Navigate } from "react-router-dom"
import { TopBar } from "./TopBar"
import { useAuth } from "../contexts/AuthContext"
import { Dashboard } from "../features/purchase-contract/Dashboard"
import { PurchaseContractList } from "../features/purchase-contract/PurchaseContractList"
import { PurchaseContractForm } from "../features/purchase-contract/PurchaseContractForm"
import { PurchaseContractDetail } from "../features/purchase-contract/PurchaseContractDetail"
import { SalesContractList } from "../features/sales-contract/SalesContractList"
import { SalesContractForm } from "../features/sales-contract/SalesContractForm"
import { SalesContractDetail } from "../features/sales-contract/SalesContractDetail"
import { EnterpriseList } from "../features/basedata/EnterpriseList"
import { CommissionPlatformList } from "../features/basedata/CommissionPlatformList"
import { CompanyList } from "../features/basedata/CompanyList"
import { BrandManage } from "../features/brand/BrandManage"
import { RecycleBin } from "../features/recycle-bin/RecycleBin"
import { UserList } from "../features/auth/UserList"
import { RoleList } from "../features/auth/RoleList"
import { PermissionList } from "../features/auth/PermissionList"
import { ShippingPlanKanban } from "../features/shipping/ShippingPlanKanban"
import { ShippingPlanForm } from "../features/shipping/ShippingPlanForm"
import { FreightLedger } from "../features/freight/FreightLedger"
import { FinanceDashboard } from "../features/finance/FinanceDashboard"
import { ReceiptForm } from "../features/finance/ReceiptForm"
import { PaymentForm } from "../features/finance/PaymentForm"
import { ARLedger } from "../features/finance/ARLedger"
import { APLedger } from "../features/finance/APLedger"
import { OCRConfig } from "../features/system/OCRConfig"

function ProtectedRoute({ perm, children }: { perm: string; children: React.ReactNode }) {
  const { hasPermission } = useAuth()
  if (!hasPermission(perm)) return <div className="flex items-center justify-center h-96 text-slate-400 text-sm">403 · 无权限访问</div>
  return <>{children}</>
}

export function AppShell() {
  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <TopBar />
      <main className="flex-1 overflow-x-hidden w-full min-w-0">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/purchase-contracts" element={<PurchaseContractList />} />
          <Route path="/purchase-contracts/create" element={<PurchaseContractForm />} />
          <Route path="/purchase-contracts/:id" element={<PurchaseContractDetail />} />
          <Route path="/purchase-contracts/:id/edit" element={<PurchaseContractForm />} />
          <Route path="/sales-contracts" element={<SalesContractList />} />
          <Route path="/sales-contracts/create" element={<SalesContractForm />} />
          <Route path="/sales-contracts/:id" element={<SalesContractDetail />} />
          <Route path="/sales-contracts/:id/edit" element={<SalesContractForm />} />
          <Route path="/shipping/plans" element={<ShippingPlanKanban />} />
          <Route path="/shipping/plans/create" element={<ShippingPlanForm />} />
          <Route path="/freight" element={<FreightLedger />} />
          <Route path="/finance" element={<FinanceDashboard />} />
          <Route path="/finance/ar" element={<ARLedger />} />
          <Route path="/finance/ap" element={<APLedger />} />
          <Route path="/finance/ar/new" element={<ReceiptForm />} />
          <Route path="/finance/ap/new" element={<PaymentForm />} />
          <Route path="/system/ocr" element={<OCRConfig />} />
          <Route path="/basedata/enterprises" element={<EnterpriseList />} />
          <Route path="/basedata/commission-platforms" element={<CommissionPlatformList />} />
          <Route path="/basedata/companies" element={<CompanyList />} />
          <Route path="/brand" element={<BrandManage />} />
          <Route path="/recycle-bin" element={<RecycleBin />} />
          <Route path="/auth/users" element={<ProtectedRoute perm="auth.user.read"><UserList /></ProtectedRoute>} />
          <Route path="/auth/roles" element={<ProtectedRoute perm="auth.role.manage"><RoleList /></ProtectedRoute>} />
          <Route path="/auth/permissions" element={<ProtectedRoute perm="auth.role.manage"><PermissionList /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
