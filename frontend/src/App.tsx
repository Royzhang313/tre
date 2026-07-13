import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { PortalProvider } from "./contexts/PortalContext"
import { AuthProvider, useAuth } from "./contexts/AuthContext"
import { ToastProvider, ConfirmProvider } from "./components/shared/Dialog"
import { AppShell } from "./components/AppShell"
import { LoginPage } from "./features/auth/LoginPage"
import { ProductList } from "./features/product/ProductList"
import { ProductForm } from "./features/product/ProductForm"
import { ContractStockList } from "./features/inventory/ContractStockList"

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 30000 } } })

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <PortalProvider>
            <ToastProvider>
            <ConfirmProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/*" element={<AuthGuard><AppShell /></AuthGuard>} />
              {/* Product Routes */}
              <Route path="/products" element={<AuthGuard><ProductList /></AuthGuard>} />
              <Route path="/products/new" element={<AuthGuard><ProductForm /></AuthGuard>} />
              <Route path="/products/:id/edit" element={<AuthGuard><ProductForm /></AuthGuard>} />
              {/* Inventory Routes */}
              <Route path="/inventory" element={<AuthGuard><ContractStockList /></AuthGuard>} />
            </Routes>
            </ConfirmProvider>
            </ToastProvider>
          </PortalProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
