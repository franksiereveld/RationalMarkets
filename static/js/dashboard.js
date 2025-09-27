// AI Long/Short Strategy MVP Dashboard JavaScript

class Dashboard {
    constructor() {
        this.isDemo = false;
        this.currentOrders = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.updateAllocationDisplay();
    }

    setupEventListeners() {
        // Portfolio allocation controls
        const allocationSlider = document.getElementById('allocationPercentage');
        const portfolioValue = document.getElementById('portfolioValue');
        
        allocationSlider.addEventListener('input', () => this.updateAllocationDisplay());
        portfolioValue.addEventListener('input', () => this.updateAllocationDisplay());
        
        // Calculate orders button
        document.getElementById('calculateOrders').addEventListener('click', () => this.calculateOrders());
        
        // Execute orders button
        document.getElementById('executeOrders').addEventListener('click', () => this.executeOrders());
        
        // Export orders button
        document.getElementById('exportOrders').addEventListener('click', () => this.exportOrders());
        
        // Refresh performance button
        document.getElementById('refreshPerformance').addEventListener('click', () => this.refreshPerformance());
        
        // Modal close
        document.querySelector('.close').addEventListener('click', () => this.closeModal());
        window.addEventListener('click', (e) => {
            if (e.target === document.getElementById('resultsModal')) {
                this.closeModal();
            }
        });
    }

    async loadInitialData() {
        await Promise.all([
            this.loadStrategyInfo(),
            this.loadAccountStatus()
        ]);
    }

    async loadStrategyInfo() {
        try {
            const response = await fetch('/api/strategy/summary');
            const data = await response.json();
            
            if (data.error) {
                this.showDemoMode();
                this.displayDemoStrategy();
            } else {
                this.displayStrategyInfo(data);
            }
        } catch (error) {
            console.error('Error loading strategy info:', error);
            this.showDemoMode();
            this.displayDemoStrategy();
        }
    }

    async loadAccountStatus() {
        try {
            const response = await fetch('/api/account/status');
            const data = await response.json();
            
            this.isDemo = data.demo_mode;
            this.brokerInfo = data.broker || {};
            this.displayAccountInfo(data.account);
            this.updateBrokerDisplay(data.broker);
            this.updateConnectionStatus();
        } catch (error) {
            console.error('Error loading account status:', error);
            this.showError('Failed to load account information');
        }
    }

    displayStrategyInfo(data) {
        const container = document.getElementById('strategyInfo');
        
        const longPositions = data.positions.filter(p => p.side === 'long');
        const shortPositions = data.positions.filter(p => p.side === 'short');
        
        container.innerHTML = `
            <div class="strategy-grid">
                <div class="strategy-stat">
                    <span class="value">${data.total_positions}</span>
                    <span class="label">Total Positions</span>
                </div>
                <div class="strategy-stat">
                    <span class="value">${longPositions.length}</span>
                    <span class="label">Long Positions</span>
                </div>
                <div class="strategy-stat">
                    <span class="value">${shortPositions.length}</span>
                    <span class="label">Short Positions</span>
                </div>
                <div class="strategy-stat">
                    <span class="value">${(data.avg_confidence * 100).toFixed(1)}%</span>
                    <span class="label">Avg Confidence</span>
                </div>
            </div>
            
            <div style="margin-top: 24px;">
                <h3 style="margin-bottom: 16px; color: var(--primary-color);">Current Positions</h3>
                ${data.positions.map(pos => `
                    <div class="position-item">
                        <div>
                            <span class="position-symbol">${pos.symbol}</span>
                            <span class="position-side ${pos.side}">${pos.side.toUpperCase()}</span>
                        </div>
                        <div class="position-details">
                            <div class="position-weight">${(pos.weight * 100).toFixed(1)}%</div>
                            <div class="position-rationale">${pos.rationale}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    displayDemoStrategy() {
        const container = document.getElementById('strategyInfo');
        container.innerHTML = `
            <div class="demo-warning">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Running in demo mode. Connect your Alpaca API keys for live data.</span>
            </div>
            <div class="strategy-grid">
                <div class="strategy-stat">
                    <span class="value">10</span>
                    <span class="label">Total Positions</span>
                </div>
                <div class="strategy-stat">
                    <span class="value">5</span>
                    <span class="label">Long Positions</span>
                </div>
                <div class="strategy-stat">
                    <span class="value">5</span>
                    <span class="label">Short Positions</span>
                </div>
                <div class="strategy-stat">
                    <span class="value">85.0%</span>
                    <span class="label">Avg Confidence</span>
                </div>
            </div>
        `;
    }

    displayAccountInfo(account) {
        const container = document.getElementById('accountInfo');
        
        container.innerHTML = `
            ${this.isDemo ? '<div class="demo-warning"><i class="fas fa-exclamation-triangle"></i><span>Demo account - not connected to real trading</span></div>' : ''}
            <div class="account-grid">
                <div class="account-item">
                    <span class="value">$${this.formatNumber(account.portfolio_value)}</span>
                    <span class="label">Portfolio Value</span>
                </div>
                <div class="account-item">
                    <span class="value">$${this.formatNumber(account.buying_power)}</span>
                    <span class="label">Buying Power</span>
                </div>
                <div class="account-item">
                    <span class="value">$${this.formatNumber(account.cash)}</span>
                    <span class="label">Cash</span>
                </div>
                <div class="account-item">
                    <span class="value">${account.status}</span>
                    <span class="label">Status</span>
                </div>
            </div>
        `;
    }

    updateConnectionStatus() {
        const statusElement = document.getElementById('connectionStatus');
        
        if (this.isDemo) {
            statusElement.className = 'status-indicator demo';
            statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Demo Mode</span>';
        } else {
            statusElement.className = 'status-indicator connected';
            statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Connected</span>';
        }
    }

    updateAllocationDisplay() {
        const allocationSlider = document.getElementById('allocationPercentage');
        const portfolioValue = document.getElementById('portfolioValue');
        const allocationValue = document.getElementById('allocationValue');
        const allocatedAmount = document.getElementById('allocatedAmount');
        
        const percentage = parseInt(allocationSlider.value);
        const totalValue = parseFloat(portfolioValue.value) || 0;
        const allocated = totalValue * percentage / 100;
        
        allocationValue.textContent = `${percentage}%`;
        allocatedAmount.textContent = `$${this.formatNumber(allocated)}`;
    }

    async calculateOrders() {
        const button = document.getElementById('calculateOrders');
        const originalText = button.innerHTML;
        
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculating...';
        
        try {
            const portfolioValue = parseFloat(document.getElementById('portfolioValue').value);
            const allocationPercentage = parseInt(document.getElementById('allocationPercentage').value);
            
            const response = await fetch('/api/portfolio/allocate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: 'demo_user',
                    allocation_percentage: allocationPercentage,
                    total_portfolio_value: portfolioValue
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
            } else {
                this.currentOrders = data.orders;
                this.displayOrders(data.orders, data.demo_mode);
            }
        } catch (error) {
            console.error('Error calculating orders:', error);
            this.showError('Failed to calculate orders');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    displayOrders(orders, demoMode = false) {
        const container = document.getElementById('ordersContainer');
        const actionsContainer = document.getElementById('ordersActions');
        
        if (orders.length === 0) {
            container.innerHTML = '<p>No orders generated.</p>';
            actionsContainer.style.display = 'none';
            return;
        }
        
        const totalLong = orders.filter(o => o.side === 'buy').reduce((sum, o) => sum + o.dollar_amount, 0);
        const totalShort = orders.filter(o => o.side === 'sell').reduce((sum, o) => sum + o.dollar_amount, 0);
        
        container.innerHTML = `
            ${demoMode ? '<div class="demo-warning"><i class="fas fa-exclamation-triangle"></i><span>Demo orders - using simulated prices</span></div>' : ''}
            
            <div class="strategy-grid" style="margin-bottom: 20px;">
                <div class="strategy-stat">
                    <span class="value">${orders.length}</span>
                    <span class="label">Total Orders</span>
                </div>
                <div class="strategy-stat">
                    <span class="value">$${this.formatNumber(totalLong)}</span>
                    <span class="label">Long Positions</span>
                </div>
                <div class="strategy-stat">
                    <span class="value">$${this.formatNumber(totalShort)}</span>
                    <span class="label">Short Positions</span>
                </div>
                <div class="strategy-stat">
                    <span class="value">$${this.formatNumber(totalLong + totalShort)}</span>
                    <span class="label">Total Allocation</span>
                </div>
            </div>
            
            <table class="orders-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Amount</th>
                        <th>Weight</th>
                        <th>Rationale</th>
                    </tr>
                </thead>
                <tbody>
                    ${orders.map(order => `
                        <tr>
                            <td><strong>${order.symbol}</strong></td>
                            <td><span class="side-${order.side}">${order.side.toUpperCase()}</span></td>
                            <td>${order.quantity.toFixed(6)}</td>
                            <td>$${order.current_price.toFixed(2)}</td>
                            <td>$${this.formatNumber(order.dollar_amount)}</td>
                            <td>${(order.weight * 100).toFixed(1)}%</td>
                            <td style="max-width: 200px; font-size: 0.9rem;">${order.rationale}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        actionsContainer.style.display = 'flex';
        
        // Update execute button based on demo mode
        const executeButton = document.getElementById('executeOrders');
        if (demoMode) {
            executeButton.innerHTML = '<i class="fas fa-eye"></i> Preview Execution (Demo)';
            executeButton.className = 'btn btn-secondary';
        } else {
            executeButton.innerHTML = '<i class="fas fa-play"></i> Execute All Orders';
            executeButton.className = 'btn btn-success';
        }
    }

    async executeOrders() {
        if (this.currentOrders.length === 0) {
            this.showError('No orders to execute');
            return;
        }
        
        const button = document.getElementById('executeOrders');
        const originalText = button.innerHTML;
        
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executing...';
        
        try {
            if (this.isDemo) {
                // Demo mode - simulate execution
                this.showExecutionResults(this.simulateExecution(this.currentOrders));
            } else {
                // Real execution
                const response = await fetch('/api/orders/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        orders: this.currentOrders
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    this.showError(data.error);
                } else {
                    this.showExecutionResults(data.results);
                    // Refresh performance after execution
                    setTimeout(() => this.refreshPerformance(), 2000);
                }
            }
        } catch (error) {
            console.error('Error executing orders:', error);
            this.showError('Failed to execute orders');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    simulateExecution(orders) {
        return orders.map(order => ({
            symbol: order.symbol,
            side: order.side,
            quantity: order.quantity,
            dollar_amount: order.dollar_amount,
            status: 'simulated',
            order_id: 'demo_' + Math.random().toString(36).substr(2, 9),
            submitted_at: new Date().toISOString(),
            rationale: order.rationale
        }));
    }

    showExecutionResults(results) {
        const modal = document.getElementById('resultsModal');
        const modalBody = document.getElementById('modalBody');
        
        const successful = results.filter(r => r.status === 'submitted' || r.status === 'simulated');
        const failed = results.filter(r => r.status === 'failed');
        
        modalBody.innerHTML = `
            <div class="strategy-grid" style="margin-bottom: 20px;">
                <div class="strategy-stat">
                    <span class="value">${results.length}</span>
                    <span class="label">Total Orders</span>
                </div>
                <div class="strategy-stat">
                    <span class="value" style="color: var(--success-color);">${successful.length}</span>
                    <span class="label">Successful</span>
                </div>
                <div class="strategy-stat">
                    <span class="value" style="color: var(--danger-color);">${failed.length}</span>
                    <span class="label">Failed</span>
                </div>
                <div class="strategy-stat">
                    <span class="value">$${this.formatNumber(successful.reduce((sum, r) => sum + r.dollar_amount, 0))}</span>
                    <span class="label">Total Executed</span>
                </div>
            </div>
            
            <h4 style="margin-bottom: 16px;">Order Details</h4>
            ${results.map(result => `
                <div class="position-item" style="margin-bottom: 12px;">
                    <div>
                        <span class="position-symbol">${result.symbol}</span>
                        <span class="position-side ${result.side}">${result.side.toUpperCase()}</span>
                        <span style="margin-left: 12px; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; 
                              background: ${result.status === 'failed' ? 'var(--danger-color)' : 'var(--success-color)'}; 
                              color: white;">${result.status.toUpperCase()}</span>
                    </div>
                    <div class="position-details">
                        <div class="position-weight">$${this.formatNumber(result.dollar_amount)}</div>
                        <div class="position-rationale">${result.quantity.toFixed(6)} shares</div>
                        ${result.error ? `<div style="color: var(--danger-color); font-size: 0.8rem;">${result.error}</div>` : ''}
                    </div>
                </div>
            `).join('')}
        `;
        
        modal.style.display = 'block';
    }

    async refreshPerformance() {
        const button = document.getElementById('refreshPerformance');
        const originalText = button.innerHTML;
        
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        
        try {
            const portfolioValue = parseFloat(document.getElementById('portfolioValue').value);
            const allocationPercentage = parseInt(document.getElementById('allocationPercentage').value);
            
            const response = await fetch(`/api/portfolio/performance?allocation_percentage=${allocationPercentage}&total_portfolio_value=${portfolioValue}`);
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
            } else {
                this.displayPerformance(data);
            }
        } catch (error) {
            console.error('Error refreshing performance:', error);
            this.showError('Failed to refresh performance');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    displayPerformance(data) {
        const container = document.getElementById('performanceContainer');
        const refreshButton = document.getElementById('refreshPerformance');
        
        container.innerHTML = `
            <div class="performance-grid">
                <div class="performance-item">
                    <span class="value">$${this.formatNumber(data.allocated_amount)}</span>
                    <span class="label">Allocated Amount</span>
                </div>
                <div class="performance-item">
                    <span class="value">$${this.formatNumber(data.current_market_value || 0)}</span>
                    <span class="label">Current Value</span>
                </div>
                <div class="performance-item">
                    <span class="value ${data.unrealized_pl >= 0 ? 'positive' : 'negative'}">
                        $${this.formatNumber(data.unrealized_pl || 0)}
                    </span>
                    <span class="label">Unrealized P&L</span>
                </div>
                <div class="performance-item">
                    <span class="value ${data.total_return_pct >= 0 ? 'positive' : 'negative'}">
                        ${(data.total_return_pct || 0).toFixed(2)}%
                    </span>
                    <span class="label">Total Return</span>
                </div>
            </div>
            
            ${data.positions && data.positions.length > 0 ? `
                <h4 style="margin: 24px 0 16px 0;">Current Positions</h4>
                ${data.positions.map(pos => `
                    <div class="position-item">
                        <div>
                            <span class="position-symbol">${pos.symbol}</span>
                            <span class="position-side ${pos.side}">${pos.side.toUpperCase()}</span>
                        </div>
                        <div class="position-details">
                            <div class="position-weight">$${this.formatNumber(pos.market_value)}</div>
                            <div class="position-rationale ${pos.unrealized_pl >= 0 ? 'positive' : 'negative'}">
                                ${pos.unrealized_pl >= 0 ? '+' : ''}$${this.formatNumber(pos.unrealized_pl)} 
                                (${(pos.unrealized_plpc * 100).toFixed(2)}%)
                            </div>
                        </div>
                    </div>
                `).join('')}
            ` : ''}
        `;
        
        refreshButton.style.display = 'block';
    }

    exportOrders() {
        if (this.currentOrders.length === 0) {
            this.showError('No orders to export');
            return;
        }
        
        const csv = this.ordersToCSV(this.currentOrders);
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ai-longshort-orders-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    ordersToCSV(orders) {
        const headers = ['Symbol', 'Side', 'Quantity', 'Price', 'Amount', 'Weight', 'Rationale'];
        const rows = orders.map(order => [
            order.symbol,
            order.side,
            order.quantity.toFixed(6),
            order.current_price.toFixed(2),
            order.dollar_amount.toFixed(2),
            (order.weight * 100).toFixed(1) + '%',
            `"${order.rationale}"`
        ]);
        
        return [headers, ...rows].map(row => row.join(',')).join('\n');
    }

    closeModal() {
        document.getElementById('resultsModal').style.display = 'none';
    }

    showDemoMode() {
        this.isDemo = true;
        this.updateConnectionStatus();
    }

    showError(message) {
        // Simple error display - could be enhanced with a proper notification system
        alert(`Error: ${message}`);
    }

    formatNumber(num) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(num);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});


    updateBrokerDisplay(broker) {
        if (broker) {
            // Update footer
            const footerBroker = document.getElementById('footer-broker');
            if (footerBroker) {
                footerBroker.textContent = `${broker.name} (${broker.region})`;
            }
            
            // Update connection status text
            const statusElement = document.getElementById('connectionStatus');
            if (statusElement) {
                const statusText = statusElement.querySelector('span');
                if (statusText) {
                    statusText.textContent = `Connected to ${broker.name}`;
                }
            }
        }
    }


// Disclaimer Functions
function showFullDisclaimer() {
    document.getElementById('disclaimerModal').style.display = 'block';
}

function closeDisclaimer() {
    document.getElementById('disclaimerModal').style.display = 'none';
}

// Show disclaimer on first visit
document.addEventListener('DOMContentLoaded', function() {
    // Check if user has seen disclaimer before
    const hasSeenDisclaimer = localStorage.getItem('hasSeenDisclaimer');
    
    if (!hasSeenDisclaimer) {
        // Show disclaimer after a short delay
        setTimeout(() => {
            showFullDisclaimer();
            localStorage.setItem('hasSeenDisclaimer', 'true');
        }, 2000);
    }
});

// Add disclaimer acknowledgment to order execution
const originalExecuteOrders = Dashboard.prototype.executeOrders;
Dashboard.prototype.executeOrders = function() {
    // Show confirmation with disclaimer
    const confirmed = confirm(
        "IMPORTANT DISCLAIMER: This is a demo execution for educational purposes only. " +
        "No real trades will be executed through this platform. " +
        "All actual trading must be done independently through your chosen broker. " +
        "Do you understand this is for educational demonstration only?"
    );
    
    if (confirmed) {
        originalExecuteOrders.call(this);
    }
};

// Add disclaimer to order calculation
const originalCalculateOrders = Dashboard.prototype.calculateOrders;
Dashboard.prototype.calculateOrders = function() {
    // Add educational notice
    const ordersContainer = document.getElementById('ordersContainer');
    
    originalCalculateOrders.call(this);
    
    // Add disclaimer after orders are displayed
    setTimeout(() => {
        const existingDisclaimer = ordersContainer.querySelector('.orders-educational-notice');
        if (!existingDisclaimer && this.currentOrders.length > 0) {
            const disclaimer = document.createElement('div');
            disclaimer.className = 'orders-educational-notice';
            disclaimer.innerHTML = `
                <div style="background: #FFF5B7; border: 1px solid #D69E2E; border-radius: 8px; padding: 15px; margin: 15px 0;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <i class="fas fa-graduation-cap" style="color: #D69E2E; font-size: 1.2em;"></i>
                        <div>
                            <strong>Educational Example:</strong> These orders are generated for learning purposes only. 
                            They do not constitute investment recommendations. Conduct your own research and consult 
                            qualified professionals before making any investment decisions.
                        </div>
                    </div>
                </div>
            `;
            ordersContainer.appendChild(disclaimer);
        }
    }, 100);
};

// Enhanced modal display with disclaimers
const originalShowModal = Dashboard.prototype.showModal;
Dashboard.prototype.showModal = function(title, content) {
    // Add disclaimer to modal content
    const disclaimerContent = `
        <div style="background: #FED7D7; border: 1px solid #E53E3E; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-exclamation-triangle" style="color: #E53E3E; font-size: 1.2em;"></i>
                <div>
                    <strong>Educational Platform Notice:</strong> All results shown are for educational demonstration only. 
                    This platform does not execute real trades or provide investment advice.
                </div>
            </div>
        </div>
        ${content}
    `;
    
    originalShowModal.call(this, title, disclaimerContent);
};


// Broker Management Functions
let currentBroker = 'alpaca'; // Default broker
let brokerConnections = {
    alpaca: { connected: false, credentials: null },
    swissquote: { connected: false, credentials: null }
};

function switchBroker() {
    const brokerSelect = document.getElementById('brokerSelect');
    currentBroker = brokerSelect.value;
    
    // Update UI based on selected broker
    updateBrokerUI();
    
    // Reload strategy and account info for new broker
    loadStrategyInfo();
    loadAccountStatus();
    
    // Clear any existing orders
    document.getElementById('ordersContainer').innerHTML = '';
    
    console.log(`Switched to ${currentBroker} broker`);
}

function updateBrokerUI() {
    const connection = brokerConnections[currentBroker];
    const setupBtn = document.getElementById('brokerSetupBtn');
    
    if (connection.connected) {
        setupBtn.innerHTML = '<i class="fas fa-check-circle"></i> Connected';
        setupBtn.style.background = '#38A169';
    } else {
        setupBtn.innerHTML = '<i class="fas fa-cog"></i> Setup';
        setupBtn.style.background = '#D69E2E';
    }
}

function showBrokerSetup() {
    const modal = document.getElementById('brokerSetupModal');
    const alpacaSetup = document.getElementById('alpacaSetup');
    const swissquoteSetup = document.getElementById('swissquoteSetup');
    
    // Show appropriate setup content
    if (currentBroker === 'alpaca') {
        alpacaSetup.style.display = 'block';
        swissquoteSetup.style.display = 'none';
    } else {
        alpacaSetup.style.display = 'none';
        swissquoteSetup.style.display = 'block';
    }
    
    modal.style.display = 'block';
}

function closeBrokerSetup() {
    document.getElementById('brokerSetupModal').style.display = 'none';
}

function connectAlpaca() {
    const apiKey = document.getElementById('alpacaApiKey').value;
    const secretKey = document.getElementById('alpacaSecretKey').value;
    const paperMode = document.getElementById('alpacaPaperMode').checked;
    
    if (!apiKey || !secretKey) {
        alert('Please enter both API Key and Secret Key');
        return;
    }
    
    // Store credentials (in real app, this would be encrypted)
    brokerConnections.alpaca.credentials = {
        apiKey: apiKey,
        secretKey: secretKey,
        paperMode: paperMode
    };
    
    // Test connection
    testBrokerConnection('alpaca')
        .then(success => {
            if (success) {
                brokerConnections.alpaca.connected = true;
                updateBrokerUI();
                closeBrokerSetup();
                
                // Show success message
                showConnectionStatus('alpaca', 'connected', 'Successfully connected to Alpaca!');
                
                // Reload data with new connection
                loadStrategyInfo();
                loadAccountStatus();
            } else {
                showConnectionStatus('alpaca', 'disconnected', 'Failed to connect to Alpaca. Please check your credentials.');
            }
        });
}

function connectSwissquote() {
    const clientId = document.getElementById('swissquoteClientId').value;
    const clientSecret = document.getElementById('swissquoteClientSecret').value;
    const demoMode = document.getElementById('swissquoteDemoMode').checked;
    
    if (!clientId || !clientSecret) {
        alert('Please enter both Client ID and Client Secret');
        return;
    }
    
    // Store credentials (in real app, this would be encrypted)
    brokerConnections.swissquote.credentials = {
        clientId: clientId,
        clientSecret: clientSecret,
        demoMode: demoMode
    };
    
    // Test connection
    testBrokerConnection('swissquote')
        .then(success => {
            if (success) {
                brokerConnections.swissquote.connected = true;
                updateBrokerUI();
                closeBrokerSetup();
                
                // Show success message
                showConnectionStatus('swissquote', 'connected', 'Successfully connected to Swissquote!');
                
                // Reload data with new connection
                loadStrategyInfo();
                loadAccountStatus();
            } else {
                showConnectionStatus('swissquote', 'disconnected', 'Failed to connect to Swissquote. Please check your credentials.');
            }
        });
}

async function testBrokerConnection(broker) {
    try {
        const response = await fetch('/api/test-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                broker: broker,
                credentials: brokerConnections[broker].credentials
            })
        });
        
        const result = await response.json();
        return result.success;
    } catch (error) {
        console.error('Connection test failed:', error);
        return false;
    }
}

function showConnectionStatus(broker, status, message) {
    // Create status indicator
    const statusDiv = document.createElement('div');
    statusDiv.className = `connection-status ${status}`;
    statusDiv.innerHTML = `
        <i class="fas fa-${status === 'connected' ? 'check-circle' : 'exclamation-triangle'}"></i>
        ${message}
    `;
    
    // Add to appropriate setup section
    const setupSection = broker === 'alpaca' ? 
        document.getElementById('alpacaSetup') : 
        document.getElementById('swissquoteSetup');
    
    // Remove any existing status
    const existingStatus = setupSection.querySelector('.connection-status');
    if (existingStatus) {
        existingStatus.remove();
    }
    
    // Add new status
    setupSection.appendChild(statusDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (statusDiv.parentNode) {
            statusDiv.remove();
        }
    }, 5000);
}

// Enhanced order calculation with broker-specific logic
const originalCalculateOrdersEnhanced = Dashboard.prototype.calculateOrders;
Dashboard.prototype.calculateOrders = async function() {
    const portfolioValue = parseFloat(document.getElementById('portfolioValue').value);
    const allocationPercentage = parseFloat(document.getElementById('allocationPercentage').value);
    
    if (!portfolioValue || portfolioValue <= 0) {
        alert('Please enter a valid portfolio value');
        return;
    }
    
    try {
        const response = await fetch('/api/calculate-orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                broker: currentBroker,
                portfolio_value: portfolioValue,
                allocation_percentage: allocationPercentage,
                credentials: brokerConnections[currentBroker].credentials
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            this.currentOrders = result.orders;
            this.displayOrders(result.orders);
            
            // Add broker-specific disclaimer
            const ordersContainer = document.getElementById('ordersContainer');
            const brokerNotice = document.createElement('div');
            brokerNotice.className = 'broker-notice';
            brokerNotice.innerHTML = `
                <div style="background: #E6FFFA; border: 1px solid #38A169; border-radius: 8px; padding: 15px; margin: 15px 0;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <i class="fas fa-info-circle" style="color: #38A169; font-size: 1.2em;"></i>
                        <div>
                            <strong>Broker: ${currentBroker.charAt(0).toUpperCase() + currentBroker.slice(1)}</strong><br>
                            Orders calculated for ${currentBroker === 'alpaca' ? 'US markets via Alpaca' : 'global markets via Swissquote'}. 
                            ${brokerConnections[currentBroker].connected ? 'Connected and ready for execution.' : 'Demo mode - no real execution.'}
                        </div>
                    </div>
                </div>
            `;
            ordersContainer.appendChild(brokerNotice);
        } else {
            alert('Failed to calculate orders: ' + result.error);
        }
    } catch (error) {
        console.error('Error calculating orders:', error);
        alert('Error calculating orders. Please try again.');
    }
};

// Enhanced order execution with broker-specific logic
const originalExecuteOrdersEnhanced = Dashboard.prototype.executeOrders;
Dashboard.prototype.executeOrders = async function() {
    if (!this.currentOrders || this.currentOrders.length === 0) {
        alert('No orders to execute. Please calculate orders first.');
        return;
    }
    
    const connection = brokerConnections[currentBroker];
    const isDemo = !connection.connected || 
                   (currentBroker === 'alpaca' && connection.credentials?.paperMode) ||
                   (currentBroker === 'swissquote' && connection.credentials?.demoMode);
    
    // Enhanced confirmation with broker-specific information
    const confirmed = confirm(
        `Execute ${this.currentOrders.length} orders via ${currentBroker.charAt(0).toUpperCase() + currentBroker.slice(1)}?\n\n` +
        `Mode: ${isDemo ? 'DEMO/PAPER TRADING' : 'LIVE TRADING'}\n` +
        `Broker: ${currentBroker === 'alpaca' ? 'Alpaca Markets' : 'Swissquote'}\n\n` +
        `${isDemo ? 'This is for educational demonstration only.' : 'WARNING: This will execute real trades!'}`
    );
    
    if (!confirmed) return;
    
    try {
        const response = await fetch('/api/execute-orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                broker: currentBroker,
                orders: this.currentOrders,
                credentials: connection.credentials
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            this.showModal('Order Execution Results', this.formatExecutionResults(result.results));
        } else {
            alert('Failed to execute orders: ' + result.error);
        }
    } catch (error) {
        console.error('Error executing orders:', error);
        alert('Error executing orders. Please try again.');
    }
};

// Initialize broker UI on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set default broker
    document.getElementById('brokerSelect').value = currentBroker;
    updateBrokerUI();
    
    // Load saved credentials from localStorage (if any)
    const savedAlpaca = localStorage.getItem('alpacaCredentials');
    const savedSwissquote = localStorage.getItem('swissquoteCredentials');
    
    if (savedAlpaca) {
        try {
            brokerConnections.alpaca.credentials = JSON.parse(savedAlpaca);
            brokerConnections.alpaca.connected = true;
        } catch (e) {
            console.warn('Failed to load saved Alpaca credentials');
        }
    }
    
    if (savedSwissquote) {
        try {
            brokerConnections.swissquote.credentials = JSON.parse(savedSwissquote);
            brokerConnections.swissquote.connected = true;
        } catch (e) {
            console.warn('Failed to load saved Swissquote credentials');
        }
    }
    
    updateBrokerUI();
});

// Save credentials to localStorage when connected
function saveCredentials(broker) {
    const credentials = brokerConnections[broker].credentials;
    if (credentials) {
        localStorage.setItem(`${broker}Credentials`, JSON.stringify(credentials));
    }
}

// Enhanced strategy loading with broker context
const originalLoadStrategyInfo = Dashboard.prototype.loadStrategyInfo;
Dashboard.prototype.loadStrategyInfo = async function() {
    try {
        const response = await fetch(`/api/strategy/summary?broker=${currentBroker}`);
        const strategy = await response.json();
        
        const strategyInfo = document.getElementById('strategyInfo');
        strategyInfo.innerHTML = `
            <div class="strategy-stats">
                <div class="stat-item">
                    <span class="stat-label">Strategy</span>
                    <span class="stat-value">${strategy.name}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Broker</span>
                    <span class="stat-value">${currentBroker.charAt(0).toUpperCase() + currentBroker.slice(1)}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Positions</span>
                    <span class="stat-value">${strategy.total_positions}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Long/Short</span>
                    <span class="stat-value">${Math.round(strategy.target_long_allocation * 100)}%/${Math.round(strategy.target_short_allocation * 100)}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Confidence</span>
                    <span class="stat-value">${Math.round(strategy.avg_confidence)}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Base Currency</span>
                    <span class="stat-value">${strategy.base_currency || (currentBroker === 'alpaca' ? 'USD' : 'CHF')}</span>
                </div>
            </div>
            <p class="strategy-description">${strategy.description}</p>
        `;
        
        strategyInfo.classList.remove('loading');
    } catch (error) {
        console.error('Error loading strategy info:', error);
        document.getElementById('strategyInfo').innerHTML = '<p class="error">Failed to load strategy information</p>';
    }
};

