// Polpi MX - Investment Calculator

// Setup investment calculator
function setupInvestmentCalculator(listing) {
    const price = listing.price_mxn || 0;
    
    // Set default values
    const inputs = {
        price: price,
        downPayment: 20,
        interestRate: 12,
        loanTerm: 20,
        expectedRent: Math.max(15000, price * 0.006), // 0.6% of property value as monthly rent estimate
        appreciationRate: 5
    };
    
    // Populate inputs with sensible defaults
    document.getElementById('downPayment').value = inputs.downPayment;
    document.getElementById('interestRate').value = inputs.interestRate;
    document.getElementById('loanTerm').value = inputs.loanTerm;
    document.getElementById('expectedRent').value = Math.round(inputs.expectedRent);
    document.getElementById('appreciationRate').value = inputs.appreciationRate;
    
    // Add event listeners for real-time calculations
    ['downPayment', 'interestRate', 'loanTerm', 'expectedRent', 'appreciationRate'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', () => calculateInvestmentMetrics(listing));
        }
    });
    
    // Initial calculation
    calculateInvestmentMetrics(listing);
}

// Calculate investment metrics
function calculateInvestmentMetrics(listing) {
    const price = listing.price_mxn || 0;
    
    // Get input values
    const downPaymentPercent = parseFloat(document.getElementById('downPayment')?.value || 20) / 100;
    const interestRate = parseFloat(document.getElementById('interestRate')?.value || 12) / 100;
    const loanTermYears = parseFloat(document.getElementById('loanTerm')?.value || 20);
    const monthlyRent = parseFloat(document.getElementById('expectedRent')?.value || 25000);
    const appreciationRate = parseFloat(document.getElementById('appreciationRate')?.value || 5) / 100;
    
    // Calculate loan details
    const downPaymentAmount = price * downPaymentPercent;
    const loanAmount = price - downPaymentAmount;
    const monthlyInterestRate = interestRate / 12;
    const numberOfPayments = loanTermYears * 12;
    
    // Monthly payment calculation (PMT formula)
    let monthlyPayment = 0;
    if (loanAmount > 0 && monthlyInterestRate > 0) {
        monthlyPayment = loanAmount * (monthlyInterestRate * Math.pow(1 + monthlyInterestRate, numberOfPayments)) / 
                        (Math.pow(1 + monthlyInterestRate, numberOfPayments) - 1);
    }
    
    // Cash flow
    const monthlyCashFlow = monthlyRent - monthlyPayment;
    const annualCashFlow = monthlyCashFlow * 12;
    
    // Cap rate (annual rental income / property price)
    const capRate = (monthlyRent * 12) / price * 100;
    
    // Cash-on-cash return (annual cash flow / initial investment)
    const cashOnCashReturn = annualCashFlow / downPaymentAmount * 100;
    
    // Update display
    updateCalculatorResults({
        monthlyPayment,
        monthlyCashFlow,
        capRate,
        cashOnCashReturn
    });
    
    // Create equity projection chart
    createEquityChart(price, loanAmount, monthlyPayment, monthlyInterestRate, appreciationRate);
}

// Update calculator results display
function updateCalculatorResults(results) {
    const formatCurrency = (amount) => {
        const formatted = new Intl.NumberFormat('es-MX', {
            style: 'currency',
            currency: 'MXN',
            minimumFractionDigits: 0
        }).format(Math.abs(amount));
        return amount < 0 ? `-${formatted}` : formatted;
    };
    
    const formatPercentage = (percent) => {
        return `${percent.toFixed(1)}%`;
    };
    
    // Update result cards
    const monthlyPaymentEl = document.getElementById('monthlyPayment');
    if (monthlyPaymentEl) {
        monthlyPaymentEl.textContent = formatCurrency(results.monthlyPayment);
    }
    
    const cashFlowEl = document.getElementById('cashFlow');
    if (cashFlowEl) {
        cashFlowEl.textContent = formatCurrency(results.monthlyCashFlow);
        cashFlowEl.style.color = results.monthlyCashFlow >= 0 ? '#10B981' : '#EF4444';
    }
    
    const capRateEl = document.getElementById('capRate');
    if (capRateEl) {
        capRateEl.textContent = formatPercentage(results.capRate);
        capRateEl.style.color = results.capRate >= 6 ? '#10B981' : results.capRate >= 4 ? '#F59E0B' : '#EF4444';
    }
    
    const cashOnCashEl = document.getElementById('cashOnCash');
    if (cashOnCashEl) {
        cashOnCashEl.textContent = formatPercentage(results.cashOnCashReturn);
        cashOnCashEl.style.color = results.cashOnCashReturn >= 8 ? '#10B981' : results.cashOnCashReturn >= 5 ? '#F59E0B' : '#EF4444';
    }
}

// Create equity projection chart
function createEquityChart(propertyValue, initialLoanAmount, monthlyPayment, monthlyInterestRate, appreciationRate) {
    const canvas = document.getElementById('equityChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Calculate equity over 5 years
    const years = 5;
    const months = years * 12;
    const labels = [];
    const equityData = [];
    const propertyValueData = [];
    const loanBalanceData = [];
    
    let currentLoanBalance = initialLoanAmount;
    let currentPropertyValue = propertyValue;
    
    for (let month = 0; month <= months; month += 6) { // Every 6 months
        const year = month / 12;
        labels.push(year === 0 ? 'Hoy' : `Año ${year.toFixed(1)}`);
        
        // Calculate loan balance after payments
        if (month > 0 && monthlyInterestRate > 0) {
            const paymentsMade = month;
            const remainingPayments = (20 * 12) - paymentsRemaining;
            
            if (remainingPayments > 0) {
                currentLoanBalance = initialLoanAmount * 
                    ((Math.pow(1 + monthlyInterestRate, remainingPayments) - Math.pow(1 + monthlyInterestRate, paymentsRemaining)) / 
                     (Math.pow(1 + monthlyInterestRate, 20 * 12) - 1));
            } else {
                currentLoanBalance = 0;
            }
        }
        
        // Calculate property value with appreciation
        currentPropertyValue = propertyValue * Math.pow(1 + appreciationRate, year);
        
        // Calculate equity
        const equity = currentPropertyValue - currentLoanBalance;
        
        equityData.push(equity / 1000); // Convert to thousands for readability
        propertyValueData.push(currentPropertyValue / 1000);
        loanBalanceData.push(currentLoanBalance / 1000);
    }
    
    // Clear previous chart
    if (window.equityChart && typeof window.equityChart.destroy === 'function') {
        window.equityChart.destroy();
    }
    
    // Create new chart
    window.equityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Equity Total',
                    data: equityData,
                    borderColor: '#8B5CF6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Valor de la Propiedad',
                    data: propertyValueData,
                    borderColor: '#10B981',
                    backgroundColor: 'transparent',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Saldo del Préstamo',
                    data: loanBalanceData,
                    borderColor: '#EF4444',
                    backgroundColor: 'transparent',
                    tension: 0.4,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#e5e7eb',
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: '#1f2937',
                    titleColor: '#f3f4f6',
                    bodyColor: '#e5e7eb',
                    borderColor: '#374151',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + (context.parsed.y * 1000).toLocaleString('es-MX');
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                },
                y: {
                    beginAtZero: false,
                    grid: { color: '#374151' },
                    ticks: {
                        color: '#9CA3AF',
                        callback: function(value) {
                            return '$' + value.toFixed(0) + 'k';
                        }
                    }
                }
            }
        }
    });
}

// Investment recommendations based on metrics
function getInvestmentRecommendation(capRate, cashOnCashReturn, monthlyCashFlow) {
    const recommendations = [];
    
    if (capRate >= 8) {
        recommendations.push('📈 Excelente cap rate - propiedad muy rentable');
    } else if (capRate >= 6) {
        recommendations.push('✅ Buen cap rate - inversión sólida');
    } else if (capRate >= 4) {
        recommendations.push('⚠️ Cap rate promedio - evaluar otros factores');
    } else {
        recommendations.push('🔴 Cap rate bajo - considerar otras opciones');
    }
    
    if (cashOnCashReturn >= 12) {
        recommendations.push('💰 Retorno en efectivo excepcional');
    } else if (cashOnCashReturn >= 8) {
        recommendations.push('💚 Buen retorno en efectivo');
    } else if (cashOnCashReturn >= 5) {
        recommendations.push('💛 Retorno moderado');
    } else if (cashOnCashReturn <= 0) {
        recommendations.push('🔴 Flujo de efectivo negativo');
    }
    
    if (monthlyCashFlow > 5000) {
        recommendations.push('💵 Excelente flujo de efectivo mensual');
    } else if (monthlyCashFlow > 0) {
        recommendations.push('💳 Flujo de efectivo positivo');
    } else {
        recommendations.push('⚠️ Flujo de efectivo negativo - tendrás que cubrir la diferencia');
    }
    
    return recommendations;
}

// Display investment recommendations
function displayInvestmentRecommendations(capRate, cashOnCashReturn, monthlyCashFlow) {
    const recommendations = getInvestmentRecommendation(capRate, cashOnCashReturn, monthlyCashFlow);
    
    const container = document.getElementById('investmentRecommendations');
    if (!container) return;
    
    container.innerHTML = `
        <div class="investment-recommendations">
            <h4>Recomendaciones</h4>
            <ul>
                ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        </div>
    `;
}

// Add mortgage calculator helper functions
function calculateAmortizationSchedule(loanAmount, interestRate, loanTermYears) {
    const monthlyInterestRate = interestRate / 12;
    const numberOfPayments = loanTermYears * 12;
    
    const monthlyPayment = loanAmount * 
        (monthlyInterestRate * Math.pow(1 + monthlyInterestRate, numberOfPayments)) / 
        (Math.pow(1 + monthlyInterestRate, numberOfPayments) - 1);
    
    const schedule = [];
    let remainingBalance = loanAmount;
    
    for (let month = 1; month <= numberOfPayments; month++) {
        const interestPayment = remainingBalance * monthlyInterestRate;
        const principalPayment = monthlyPayment - interestPayment;
        remainingBalance -= principalPayment;
        
        schedule.push({
            month,
            payment: monthlyPayment,
            principal: principalPayment,
            interest: interestPayment,
            balance: Math.max(0, remainingBalance)
        });
        
        if (remainingBalance <= 0) break;
    }
    
    return schedule;
}

// Calculate loan balance at specific month
function calculateLoanBalanceAtMonth(loanAmount, monthlyInterestRate, monthlyPayment, monthsPassed) {
    if (monthsPassed <= 0 || monthlyInterestRate <= 0) return loanAmount;
    
    const totalPayments = 20 * 12; // 20 years
    const remainingPayments = totalPayments - monthsPassed;
    
    if (remainingPayments <= 0) return 0;
    
    // Remaining balance formula
    const balance = monthlyPayment * 
        ((Math.pow(1 + monthlyInterestRate, remainingPayments) - 1) / 
         (monthlyInterestRate * Math.pow(1 + monthlyInterestRate, remainingPayments)));
    
    return Math.max(0, balance);
}

// Export functions
if (typeof window !== 'undefined') {
    window.setupInvestmentCalculator = setupInvestmentCalculator;
    window.calculateInvestmentMetrics = calculateInvestmentMetrics;
    window.getInvestmentRecommendation = getInvestmentRecommendation;
}