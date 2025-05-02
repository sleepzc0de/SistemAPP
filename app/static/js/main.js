/**
 * APP (Assets Planning Prediction) Main JavaScript File
 * Contains shared functionality for the application
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('APP JavaScript initialized');
    
    // Initialize Bootstrap tooltips
    initTooltips();
    
    // Initialize Bootstrap popovers
    initPopovers();
    
    // Add event listeners to elements
    addEventListeners();
    
    // Check for flash message auto-dismiss
    setupFlashMessages();
    
    // Initialize any charts on the page
    initCharts();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Add event listeners to elements
 */
function addEventListeners() {
    // Add click listener for the back button
    const backButtons = document.querySelectorAll('.btn-back');
    backButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.history.back();
        });
    });
    
    // Add listener for asset code search
    const assetCodeSearchInputs = document.querySelectorAll('.asset-code-search');
    assetCodeSearchInputs.forEach(function(input) {
        input.addEventListener('input', handleAssetCodeSearch);
    });
    
    // Add listener for asset code selection
    const assetCodeSelects = document.querySelectorAll('.asset-code-select');
    assetCodeSelects.forEach(function(select) {
        select.addEventListener('change', handleAssetCodeSelect);
    });
    
    // Add listener for quantity inputs
    const quantityInputs = document.querySelectorAll('.quantity-input');
    quantityInputs.forEach(function(input) {
        input.addEventListener('input', validateQuantityInput);
    });
    
    // Add listener for form submissions
    const forms = document.querySelectorAll('form:not(.no-validation)');
    forms.forEach(function(form) {
        form.addEventListener('submit', validateForm);
    });
    
    // Add listener for asset condition updates
    const conditionSelects = document.querySelectorAll('.condition-select');
    conditionSelects.forEach(function(select) {
        select.addEventListener('change', updateAssetCondition);
    });
    
    // Add listener for print buttons
    const printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });
}

/**
 * Setup auto-dismissing flash messages
 */
function setupFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert:not(.alert-permanent)');
    flashMessages.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // Auto-dismiss after 5 seconds
    });
}

/**
 * Initialize charts on the page
 */
function initCharts() {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded');
        return;
    }
    
    // Initialize prediction distribution chart if it exists
    initPredictionDistributionChart();
    
    // Initialize monthly stats chart if it exists
    initMonthlyStatsChart();
    
    // Initialize asset condition chart if it exists
    initAssetConditionChart();
    
    // Initialize asset code chart if it exists
    initAssetCodeChart();
}

/**
 * Initialize prediction distribution chart
 */
function initPredictionDistributionChart() {
    const predictionChartElement = document.getElementById('predictionDistributionChart');
    
    if (!predictionChartElement) {
        return;
    }
    
    // Get data from data attributes
    const approved = parseInt(predictionChartElement.dataset.approved || 0);
    const rejected = parseInt(predictionChartElement.dataset.rejected || 0);
    
    const predictionChart = new Chart(predictionChartElement, {
        type: 'doughnut',
        data: {
            labels: ['Disetujui', 'Ditolak'],
            datasets: [{
                data: [approved, rejected],
                backgroundColor: ['#198754', '#dc3545'],
                borderWidth: 0
            }]
        },
        options: {