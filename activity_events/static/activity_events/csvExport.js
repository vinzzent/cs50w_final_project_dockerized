document.addEventListener('DOMContentLoaded', function () {
    // Event listener for the export CSV button
    document.getElementById('export-csv-btn').addEventListener('click', function(event) {
        event.preventDefault(); // Prevent the default button behavior
        saveFormDataAndSubmit();
    });

    function saveFormDataAndSubmit() {
        const form = document.getElementById('activity-events-form');
        const formData = new FormData(form);
        const params = new URLSearchParams(formData).toString();        
        localStorage.setItem('formParams', params);       
        form.submit();
    }

    async function initiateCSVExport(params) {
        try {
            const exportResponse = await fetch(`/export_csv/?${params}`, {
                method: 'GET',
                headers: {'Content-Type': 'application/json'},
            });
            if (!exportResponse.ok) {
                throw new Error(`HTTP error! status: ${exportResponse.status}`);
            }
            const exportData = await exportResponse.json();

            document.getElementById('export-status').textContent = 'CSV export in progress...';

            await checkCSVStatus(exportData.task_id);
        } catch (error) {
            console.error('Error initiating CSV export:', error);
            document.getElementById('export-status').textContent = 'Failed to initiate CSV export.';
        }
    }


    async function checkCSVStatus(task_id) {
        try {
            const statusResponse = await fetch(`/check_csv_status/${task_id}/`);
            const statusData = await statusResponse.json();

            if (statusData.status === 'ready') {
                // Update status message and provide download link
                document.getElementById('export-status').textContent = 'CSV is ready!';
                const downloadLink = document.getElementById('download-link');
                downloadLink.setAttribute('href', statusData.url);
                downloadLink.style.display = 'block';
                downloadLink.textContent = 'Download CSV';
            } else if (statusData.status === 'PENDING' || statusData.status === 'STARTED') {
                // CSV is still being generated, poll again after a delay                
                setTimeout(async () => {
                    await checkCSVStatus(task_id);
                }, 2000);  // Poll every 2 seconds                
            } else {
                // Handle other statuses, e.g., FAILURE
                document.getElementById('export-status').textContent = `CSV generation failed with status: ${statusData.status}`;
            }
        } catch (error) {
            console.error('Error checking CSV status:', error);
            document.getElementById('export-status').textContent = 'Error checking CSV status.';
        }
    }
    // On page load, check if there are stored form params and initiate CSV export
    const storedParams = localStorage.getItem('formParams');
    if (storedParams) {
        localStorage.removeItem('formParams'); // Clear stored data
        initiateCSVExport(storedParams);
    }
});