// src/api.ts

const API_BASE_URL = '/api';

export interface OrderRequest {
      lat: number;
      lon: number;
      subtotal: string;
}

export interface TaxBreakdown {
      name: string;
      rate: string;
      tax_amount: string;
}

export interface OrderResponse {
      id: number;
      lat: string;
      lon: string;
      subtotal: string;
      tax_amount: string;
      total_amount: string;
      timestamp: string;
      breakdown: TaxBreakdown[];
}

export interface ImportResponse {
      id: number;
      status: string;
      total_rows: number;
      processed_rows: number;
      error_rows: number;
      errors: Record<string, string>;
      created_at: string;
}

export const api = {
      async calculateTax(data: OrderRequest): Promise<OrderResponse> {
            const response = await fetch(`${API_BASE_URL}/orders/`, {
                  method: 'POST',
                  headers: {
                        'Content-Type': 'application/json',
                  },
                  body: JSON.stringify(data),
            });
            if (!response.ok) {
                  throw new Error(`API Error: ${response.statusText}`);
            }
            return response.json();
      },

      async uploadCSV(file: File): Promise<{ id: number; status: string }> {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE_URL}/orders/import_csv/`, {
                  method: 'POST',
                  body: formData,
            });
            if (!response.ok) {
                  throw new Error(`API Error: ${response.statusText}`);
            }
            return response.json();
      },

      async checkImportStatus(id: number): Promise<ImportResponse> {
            const response = await fetch(`${API_BASE_URL}/imports/${id}/`);
            if (!response.ok) {
                  throw new Error(`API Error: ${response.statusText}`);
            }
            return response.json();
      },

      async fetchOrders(page: number = 1, limit: string = '50'): Promise<{ count: number; results: OrderResponse[] }> {
            const url = `${API_BASE_URL}/orders/?page=${page}&limit=${limit}`;
            const response = await fetch(url);
            if (!response.ok) {
                  throw new Error(`API Error: ${response.statusText}`);
            }
            return response.json();
      },

      async clearOrders(): Promise<void> {
            const response = await fetch(`${API_BASE_URL}/orders/clear/`, {
                  method: 'POST'
            });
            if (!response.ok) {
                  throw new Error(`API Error: ${response.statusText}`);
            }
      }
};
