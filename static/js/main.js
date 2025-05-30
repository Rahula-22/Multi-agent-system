document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('processor-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const content = document.getElementById('content').value;
        const file = document.getElementById('file').files[0];
        const resultsElement = document.getElementById('results');
        const formatElement = document.getElementById('detected-format');
        const intentElement = document.getElementById('detected-intent');
        
        if (!content && !file) {
            resultsElement.textContent = 'Please enter content or select a file';
            return;
        }
        
        resultsElement.textContent = 'Processing...';
        formatElement.textContent = 'Detecting...';
        intentElement.textContent = 'Analyzing...';
        
        const formData = new FormData();
        if (content) {
            formData.append('content', content);
        }
        if (file) {
            formData.append('file', file);
        }
        
        // Add conversation ID if checkbox is checked
        if (document.getElementById('use-conversation-id').checked) {
            const conversationId = document.getElementById('conversation-id').value;
            if (conversationId) {
                formData.append('conversation_id', conversationId);
            }
        }
        
        fetch('/api/process', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            // Display the detected format and intent
            formatElement.textContent = data.format || 'Unknown';
            intentElement.textContent = data.processed_data?.intent || data.intent || 'Unknown';
            
            // Display alerts if available
            if (data.alerts && data.alerts.length > 0) {
                displayAlerts(data.alerts);
            }
            
            // Display summary if available
            if (data.summary) {
                displaySummary(data.summary);
            }
            
            // Display the full results
            resultsElement.textContent = JSON.stringify(data, null, 2);
            
            // Save conversation ID if available
            if (data.conversation_id) {
                localStorage.setItem('lastConversationId', data.conversation_id);
                document.getElementById('conversation-id').value = data.conversation_id;
            }
        })
        .catch(error => {
            formatElement.textContent = 'Error';
            intentElement.textContent = 'Error';
            resultsElement.textContent = 'Error: ' + error.message;
        });
    });
    
    // Fetch History Button
    document.getElementById('fetch-history-btn').addEventListener('click', function() {
        const conversationId = document.getElementById('conversation-id').value;
        const resultsElement = document.getElementById('history-results');
        
        if (!conversationId) {
            resultsElement.textContent = 'Please enter a conversation ID';
            return;
        }
        
        resultsElement.textContent = 'Fetching...';
        
        fetch(`/api/history/${conversationId}/simplified`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            // Display summary if available
            if (data.summary) {
                displaySummary(data.summary, 'history-summary');
            }
            
            // Display alerts if available
            if (data.alerts && data.alerts.length > 0) {
                displayAlerts(data.alerts, 'history-alerts');
            }
            
            resultsElement.textContent = JSON.stringify(data, null, 2);
        })
        .catch(error => {
            resultsElement.textContent = 'Error: ' + error.message;
        });
    });
    
    // Load last conversation ID if available
    const lastConversationId = localStorage.getItem('lastConversationId');
    if (lastConversationId) {
        document.getElementById('conversation-id').value = lastConversationId;
    }
    
    // Function to display alerts
    function displayAlerts(alerts, containerId = 'alerts-container') {
        // Create alerts container if it doesn't exist
        let alertsContainer = document.getElementById(containerId);
        if (!alertsContainer) {
            alertsContainer = document.createElement('div');
            alertsContainer.id = containerId;
            alertsContainer.className = 'alerts-container mt-3';
            
            // Insert after results
            const resultsContainer = document.getElementById('results').parentNode;
            resultsContainer.parentNode.insertBefore(alertsContainer, resultsContainer.nextSibling);
        }
        
        // Clear previous alerts
        alertsContainer.innerHTML = '<h6>Alerts:</h6>';
        
        // Add each alert
        alerts.forEach(alert => {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert ${getAlertClass(alert.level)}`;
            alertDiv.textContent = alert.message;
            alertsContainer.appendChild(alertDiv);
        });
    }
    
    // Function to display summary
    function displaySummary(summary, containerId = 'summary-container') {
        // Create summary container if it doesn't exist
        let summaryContainer = document.getElementById(containerId);
        if (!summaryContainer) {
            summaryContainer = document.createElement('div');
            summaryContainer.id = containerId;
            summaryContainer.className = 'summary-container mt-3 p-3 bg-light rounded';
            
            // Insert before full results
            const resultsContainer = document.getElementById('results').parentNode;
            resultsContainer.parentNode.insertBefore(summaryContainer, resultsContainer);
        }
        
        // Display summary
        summaryContainer.innerHTML = '<h6>Summary:</h6>';
        const summaryPre = document.createElement('pre');
        summaryPre.className = 'summary-text mb-0';
        summaryPre.textContent = summary;
        summaryContainer.appendChild(summaryPre);
    }
    
    // Helper function to get Bootstrap alert class
    function getAlertClass(level) {
        switch (level.toLowerCase()) {
            case 'high':
                return 'alert-danger';
            case 'medium':
                return 'alert-warning';
            case 'low':
                return 'alert-info';
            default:
                return 'alert-secondary';
        }
    }
});