import { useState, useEffect } from 'react';
import './styles.css';
import type { OrderResponse, ImportResponse } from './api';
import { api } from './api';

function App() {
  const [lat, setLat] = useState('40.7128');
  const [lon, setLon] = useState('-74.0060');
  const [subtotal, setSubtotal] = useState('100.00');
  const [calcResult, setCalcResult] = useState<OrderResponse | null>(null);
  const [calcLoading, setCalcLoading] = useState(false);

  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<ImportResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const [orders, setOrders] = useState<OrderResponse[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [displayLimit, setDisplayLimit] = useState('100');

  useEffect(() => {
    handleFetchOrders();
  }, [displayLimit]);

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCalcLoading(true);
    try {
      const res = await api.calculateTax({
        lat: parseFloat(lat),
        lon: parseFloat(lon),
        subtotal
      });
      setCalcResult(res);
      handleFetchOrders(); // Refresh table after new calculation
    } catch (err) {
      alert('Error calculating tax');
    } finally {
      setCalcLoading(false);
    }
  };

  const pollImportStatus = async (id: number) => {
    const interval = setInterval(async () => {
      try {
        const status = await api.checkImportStatus(id);
        setUploadStatus(status);
        if (status.status === 'COMPLETED' || status.status === 'FAILED') {
          clearInterval(interval);
          setIsUploading(false);
          handleFetchOrders(); // Refresh table after import completes
        }
      } catch (err) {
        clearInterval(interval);
        setIsUploading(false);
      }
    }, 2000);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploadError(null);
    setUploadStatus(null);
    setIsUploading(true);
    try {
      const res = await api.uploadCSV(file);
      pollImportStatus(res.id);
    } catch (err) {
      setUploadError('Failed to upload CSV');
      setIsUploading(false);
    }
  };

  const handleFetchOrders = async () => {
    setOrdersLoading(true);
    try {
      const limitParam = displayLimit === 'All' ? '10000' : displayLimit;
      const res = await api.fetchOrders(limitParam);
      setOrders(res.results || []);
    } catch (err) {
      console.error('Failed to load orders', err);
    } finally {
      setOrdersLoading(false);
    }
  };

  const handleClearOrders = async () => {
    if (window.confirm('Are you sure you want to delete all orders? This cannot be undone.')) {
      setOrdersLoading(true);
      try {
        await api.clearOrders();
        await handleFetchOrders();
      } catch (err) {
        alert('Failed to clear orders');
        setOrdersLoading(false);
      }
    }
  };

  const renderCalculator = () => (
    <div className="card enter-anim">
      <h2>Myttevye Tax Calculator</h2>
      <form onSubmit={handleCalculate} className="form-group">
        <label>
          Latitude:
          <input type="text" value={lat} onChange={e => setLat(e.target.value)} required />
        </label>
        <label>
          Longitude:
          <input type="text" value={lon} onChange={e => setLon(e.target.value)} required />
        </label>
        <label>
          Subtotal ($):
          <input type="text" value={subtotal} onChange={e => setSubtotal(e.target.value)} required />
        </label>
        <button type="submit" disabled={calcLoading}>
          {calcLoading ? 'Calculating...' : 'Calculate Tax'}
        </button>
      </form>

      {calcResult && (
        <div className="result-card fade-in">
          <h3>Result</h3>
          <div className="result-row space-between">
            <span>Subtotal:</span>
            <strong>${calcResult.subtotal}</strong>
          </div>
          <div className="result-row space-between">
            <span>Total Tax:</span>
            <strong>${calcResult.total_tax}</strong>
          </div>
          <div className="divider"></div>
          <div className="result-row space-between total">
            <span>Total Amount:</span>
            <strong>${calcResult.total_amount}</strong>
          </div>

          <h4 className="mt-4">Tax Breakdown</h4>
          <ul className="breakdown-list">
            {calcResult.breakdown.map((b, i) => (
              <li key={i} className="breakdown-item space-between">
                <span>{b.name} ({b.rate}):</span>
                <span>${b.tax_amount}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  const renderUploader = () => (
    <div className="card enter-anim">
      <h2>Bulk CSV Uploader</h2>
      <div className="upload-area"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]); }}>
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
          id="file-upload"
          className="hidden"
        />
        <label htmlFor="file-upload" className="upload-label">
          <div className="upload-icon">📄</div>
          {file ? file.name : 'Drag & Drop your CSV file here or Click to select'}
        </label>
      </div>
      <button onClick={handleUpload} disabled={!file || isUploading} className="mt-4 full-width">
        {isUploading ? 'Processing... Please wait' : 'Upload and Process'}
      </button>

      {uploadError && <div className="error fade-in">{uploadError}</div>}

      {uploadStatus && (
        <div className="result-card fade-in mt-4">
          <h3>Import Status: <span className={`status badge-${uploadStatus.status.toLowerCase()}`}>{uploadStatus.status}</span></h3>
          <p>Total Rows: {uploadStatus.total_rows}</p>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${uploadStatus.total_rows ? (uploadStatus.processed_rows / uploadStatus.total_rows) * 100 : 0}%` }}
            ></div>
          </div>
          <p className="mt-2 text-sm">Processed: {uploadStatus.processed_rows} | Errors: {uploadStatus.error_rows}</p>

          {uploadStatus.errors && Object.keys(uploadStatus.errors).length > 0 && (
            <div className="error-logs">
              <h4>Error Logs</h4>
              <ul className="error-list">
                {Object.entries(uploadStatus.errors).map(([row, err]) => (
                  <li key={row}><strong>Row {row}:</strong> {err as string}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderHistory = () => (
    <div className="card enter-anim full-height">
      <div className="header-row space-between items-center mb-4">
        <h2>Recent Orders Registry</h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <select
            value={displayLimit}
            onChange={(e) => setDisplayLimit(e.target.value)}
            className="input-small"
            style={{ padding: '0.4rem', borderRadius: '4px', background: 'var(--bg-glass)', color: '#fff', border: '1px solid var(--border-color)' }}
          >
            <option value="10">Show 10</option>
            <option value="50">Show 50</option>
            <option value="100">Show 100</option>
            <option value="All">Show All</option>
          </select>
          <button onClick={handleClearOrders} disabled={ordersLoading} className="btn-small" style={{ background: '#ef4444' }}>Clear</button>
          <button onClick={handleFetchOrders} disabled={ordersLoading} className="btn-small">Refresh</button>
        </div>
      </div>

      {orders.length === 0 && !ordersLoading ? (
        <div className="empty-state">No orders loaded yet. Calculate one or upload CSV.</div>
      ) : (
        <div className="table-responsive">
          <table className="history-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Location</th>
                <th>Subtotal</th>
                <th>Tax</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.id}>
                  <td>#{o.id}</td>
                  <td>{o.lat}, {o.lon}</td>
                  <td>${o.subtotal}</td>
                  <td>${o.total_tax}</td>
                  <td><strong>${o.total_amount}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  return (
    <div className="layout">
      <header className="header">
        <div className="logo-container">
          <div className="logo-icon">🌿</div>
          <h1>Instant Wellness Kits</h1>
        </div>
        <p className="subtitle">NYS Sales Tax Engine Dashboard</p>
      </header>

      <main className="dashboard-grid">
        <div className="dashboard-left">
          {renderCalculator()}
          {renderUploader()}
        </div>
        <div className="dashboard-right">
          {renderHistory()}
        </div>
      </main>

      <footer className="footer">
        <p>Instant Wellness Kits Drones © {new Date().getFullYear()} - NYC Hackathon Edition</p>
      </footer>
    </div>
  );
}

export default App;
