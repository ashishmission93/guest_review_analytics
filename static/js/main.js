document.addEventListener("DOMContentLoaded", () => {
    const alertSection = document.getElementById("alert-section");
    const avgRatingEl = document.getElementById("avg-rating");
    const mostPositiveEl = document.getElementById("most-positive");
    const mostNegativeEl = document.getElementById("most-negative");
    const reviewListEl = document.getElementById("review-list");
    const sentimentChartEl = document.getElementById("sentiment-chart");
    let sentimentChart;

    // Function to show alert messages
    function showAlert(message) {
        alertSection.textContent = message;
        alertSection.classList.remove("d-none");
    }

    // Function to clear alert messages
    function clearAlert() {
        alertSection.classList.add("d-none");
    }

    // Function to create or update sentiment chart
    function updateChart(sentimentCounts) {
        if (sentimentChart) sentimentChart.destroy();
        
        sentimentChart = new Chart(sentimentChartEl, {
            type: 'bar',
            data: {
                labels: Object.keys(sentimentCounts),
                datasets: [{
                    label: 'Sentiment Counts',
                    data: Object.values(sentimentCounts),
                    backgroundColor: ['#28a745', '#ffc107', '#dc3545'],
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Function to display review list
    function displayReviews(reviews) {
        reviewListEl.innerHTML = '';
        reviews.forEach(review => {
            const row = `
                <tr>
                    <td>${review.date}</td>
                    <td>${review.review}</td>
                    <td>${review.rating}</td>
                    <td>${review.sentiment}</td>
                    <td>${review.advanced_sentiment}</td>
                </tr>
            `;
            reviewListEl.insertAdjacentHTML("beforeend", row);
        });
    }

    // Handle form submission
    document.getElementById("upload-form").onsubmit = async function (e) {
        e.preventDefault();
        clearAlert();

        const formData = new FormData();
        const fileInput = document.getElementById("file-input");
        formData.append("file", fileInput.files[0]);

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const { error } = await response.json();
                showAlert(error);
                return;
            }

            const data = await response.json();
            avgRatingEl.textContent = data.avg_rating.toFixed(2);
            mostPositiveEl.textContent = data.most_positive_review;
            mostNegativeEl.textContent = data.most_negative_review;

            // Update chart and review list
            updateChart(data.sentiment_counts);
            displayReviews(data.reviews);

        } catch (error) {
            showAlert("An error occurred while processing the upload.");
            console.error(error);
        }
    };
});

