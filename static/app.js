// Modern Property Dashboard Application
class PropertyDashboard {
    constructor() {
        this.properties = [];
        this.charts = {};
        this.sortColumn = null;
        this.sortDirection = 'asc';

        this.initializeEventListeners();
        this.loadInitialData();
    }

    destroyCharts() {
        // Destroy all existing charts before creating new ones
        Object.keys(this.charts).forEach(chartKey => {
            if (this.charts[chartKey]) {
                this.charts[chartKey].destroy();
                this.charts[chartKey] = null;
            }
        });
    }

    initializeEventListeners() {
        // Search form
        document.getElementById('search-btn').addEventListener('click', () => this.searchProperties());

        // Quick suburb buttons
        document.querySelectorAll('.quick-suburb').forEach(button => {
            button.addEventListener('click', (e) => {
                const suburb = e.target.dataset.suburb;

                // Update active state
                document.querySelectorAll('.quick-suburb').forEach(btn => {
                    btn.classList.remove('active');
                });
                e.target.classList.add('active');

                // Set suburb and search
                document.getElementById('suburb').value = suburb;
                this.searchProperties();
            });
        });

        // Table sorting
        document.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', (e) => this.sortTable(e.target.closest('th').dataset.sort));
        });

        // Table controls
        document.getElementById('expand-all').addEventListener('click', () => this.expandAllRows());
        document.getElementById('collapse-all').addEventListener('click', () => this.collapseAllRows());

        // Modal controls
        document.getElementById('close-modal').addEventListener('click', () => this.closeModal());
        document.getElementById('property-modal').addEventListener('click', (e) => {
            if (e.target.id === 'property-modal') this.closeModal();
        });
    }

    async loadInitialData() {
        // Set initial active button
        const initialSuburb = document.getElementById('suburb').value;
        const activeButton = document.querySelector(`[data-suburb="${initialSuburb}"]`);
        if (activeButton) {
            document.querySelectorAll('.quick-suburb').forEach(btn => {
                btn.classList.remove('active');
            });
            activeButton.classList.add('active');
        }

        await this.searchProperties();
    }

    async searchProperties() {
        const suburb = document.getElementById('suburb').value.trim();
        const propertyType = document.getElementById('property-type').value;

        if (!suburb) {
            this.showError('Please enter a suburb name');
            return;
        }

        this.showLoading(true);
        this.hideError();

        try {
            console.log(`Searching for properties in: ${suburb}, type: ${propertyType}`);
            const response = await fetch(`/api/properties?suburb=${encodeURIComponent(suburb)}&property_type=${propertyType}`);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            const data = await response.json();
            this.properties = data.results || [];

            if (this.properties.length === 0) {
                this.showError(`No properties found for "${suburb}". Try a different suburb or property type.`);
                return;
            }

            console.log(`Successfully loaded ${this.properties.length} properties from ${suburb}`);

            // Update active button state
            document.querySelectorAll('.quick-suburb').forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.suburb === suburb) {
                    btn.classList.add('active');
                }
            });

            // If no quick button matches, clear all active states
            const hasActiveButton = document.querySelector('.quick-suburb.active');
            if (!hasActiveButton) {
                document.querySelectorAll('.quick-suburb').forEach(btn => {
                    btn.classList.remove('active');
                });
            }

            this.processData();
            this.renderDashboard();

        } catch (error) {
            console.error('Error fetching properties:', error);

            // Check if it's a JSON parsing error
            if (error.message.includes('Expecting value') || error.message.includes('JSON')) {
                console.error('JSON parsing error details:', {
                    message: error.message,
                    stack: error.stack,
                    suburb: suburb,
                    propertyType: propertyType
                });
                this.showError(`Failed to load properties: Invalid data format. Please try again.`);
            } else {
                this.showError(`Failed to load properties: ${error.message}`);
            }
        } finally {
            this.showLoading(false);
        }
    }

    processData() {
        // Clean and process property data
        this.properties = this.properties.map(property => {
            const attrs = property.attributes || {};

            // Clean land size
            let landSize = attrs.land_size;
            if (landSize && typeof landSize === 'string') {
                landSize = parseFloat(landSize.replace(/[^\d.]/g, ''));
            } else if (landSize === 'None' || landSize === 'nan') {
                landSize = null;
            }

            // Calculate price per square meter
            const pricePerSqm = landSize && landSize > 0 ? property.price / landSize : null;

            return {
                ...property,
                bedrooms: attrs.bedrooms || null,
                bathrooms: attrs.bathrooms || null,
                garage_spaces: attrs.garage_spaces || null,
                land_size: landSize,
                price_per_sqm: pricePerSqm,
                listing_date: new Date(property.listing_date)
            };
        });
    }

    renderDashboard() {
        this.renderStatistics();
        this.renderCharts();
        this.renderPropertiesTable();
        this.showSections();
    }

    renderStatistics() {
        const stats = this.calculateStatistics();

        document.getElementById('total-properties').textContent = stats.count;
        document.getElementById('avg-price').textContent = this.formatCurrency(stats.avgPrice);
        document.getElementById('median-price').textContent = this.formatCurrency(stats.medianPrice);
        document.getElementById('price-range').textContent = `${this.formatCurrency(stats.minPrice)} - ${this.formatCurrency(stats.maxPrice)}`;
        document.getElementById('avg-land-size').textContent = stats.avgLandSize ? `${Math.round(stats.avgLandSize)} m²` : 'N/A';
        document.getElementById('avg-price-per-sqm').textContent = stats.avgPricePerSqm ? this.formatCurrency(stats.avgPricePerSqm) : 'N/A';
    }

    calculateStatistics() {
        const prices = this.properties.map(p => p.price);
        const landSizes = this.properties.map(p => p.land_size).filter(size => size && size > 0);
        const pricePerSqm = this.properties.map(p => p.price_per_sqm).filter(price => price && price > 0);

        return {
            count: this.properties.length,
            avgPrice: this.average(prices),
            medianPrice: this.median(prices),
            minPrice: Math.min(...prices),
            maxPrice: Math.max(...prices),
            avgLandSize: landSizes.length > 0 ? this.average(landSizes) : null,
            avgPricePerSqm: pricePerSqm.length > 0 ? this.average(pricePerSqm) : null
        };
    }

    renderCharts() {
        // Destroy existing charts before creating new ones
        this.destroyCharts();

        this.renderPriceChart();
        this.renderBedroomsChart();
        this.renderLandSizeChart();
        this.renderPricePerSqmChart();
    }

    renderPriceChart() {
        const ctx = document.getElementById('price-chart').getContext('2d');

        // Create price bins
        const prices = this.properties.map(p => p.price);
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const binSize = (maxPrice - minPrice) / 8;

        const bins = [];
        const labels = [];
        for (let i = 0; i < 8; i++) {
            const binStart = minPrice + (i * binSize);
            const binEnd = binStart + binSize;
            const count = prices.filter(p => p >= binStart && p < binEnd).length;
            bins.push(count);
            labels.push(`${this.formatCurrency(binStart)} - ${this.formatCurrency(binEnd)}`);
        }

        this.charts.price = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Number of Properties',
                    data: bins,
                    backgroundColor: 'rgba(25, 118, 210, 0.6)',
                    borderColor: 'rgba(25, 118, 210, 1)',
                    borderWidth: 1,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Price Distribution',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderBedroomsChart() {
        const ctx = document.getElementById('bedrooms-chart').getContext('2d');

        // Group by bedrooms
        const bedroomGroups = {};
        this.properties.forEach(property => {
            const bedrooms = property.bedrooms || 'Unknown';
            if (!bedroomGroups[bedrooms]) {
                bedroomGroups[bedrooms] = [];
            }
            bedroomGroups[bedrooms].push(property.price);
        });

        const labels = Object.keys(bedroomGroups).sort((a, b) => {
            if (a === 'Unknown') return 1;
            if (b === 'Unknown') return -1;
            return parseInt(a) - parseInt(b);
        });

        const data = labels.map(bedrooms => {
            const prices = bedroomGroups[bedrooms];
            return prices.reduce((sum, price) => sum + price, 0) / prices.length;
        });

        this.charts.bedrooms = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Price',
                    data: data,
                    backgroundColor: 'rgba(25, 118, 210, 0.6)',
                    borderColor: 'rgba(25, 118, 210, 1)',
                    borderWidth: 1,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Average Price by Bedrooms',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => '$' + value.toLocaleString()
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderLandSizeChart() {
        const ctx = document.getElementById('land-size-chart').getContext('2d');

        const data = this.properties
            .filter(p => p.land_size && p.land_size > 0)
            .map(p => ({ x: p.land_size, y: p.price }));

        this.charts.landSize = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Properties',
                    data: data,
                    backgroundColor: 'rgba(25, 118, 210, 0.6)',
                    borderColor: 'rgba(25, 118, 210, 1)',
                    borderWidth: 1,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Land Size vs Price',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Land Size (m²)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Price ($)'
                        },
                        ticks: {
                            callback: (value) => '$' + value.toLocaleString()
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
    }

    renderPricePerSqmChart() {
        const ctx = document.getElementById('price-per-sqm-chart').getContext('2d');

        const pricePerSqm = this.properties
            .map(p => p.price_per_sqm)
            .filter(price => price && price > 0);

        if (pricePerSqm.length === 0) return;

        const min = Math.min(...pricePerSqm);
        const max = Math.max(...pricePerSqm);
        const binSize = (max - min) / 6;

        const bins = [];
        const labels = [];
        for (let i = 0; i < 6; i++) {
            const binStart = min + (i * binSize);
            const binEnd = binStart + binSize;
            const count = pricePerSqm.filter(p => p >= binStart && p < binEnd).length;
            bins.push(count);
            labels.push(`${Math.round(binStart)} - ${Math.round(binEnd)}`);
        }

        this.charts.pricePerSqm = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Number of Properties',
                    data: bins,
                    backgroundColor: 'rgba(25, 118, 210, 0.6)',
                    borderColor: 'rgba(25, 118, 210, 1)',
                    borderWidth: 1,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Price per m² Distribution',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderPropertiesTable() {
        const tbody = document.getElementById('properties-tbody');
        tbody.innerHTML = '';

        this.properties.forEach((property, index) => {
            const row = this.createPropertyRow(property, index);
            tbody.appendChild(row);
        });

        document.getElementById('table-count').textContent = `${this.properties.length} properties`;
    }

    createPropertyRow(property, index) {
        const row = document.createElement('tr');
        row.dataset.index = index;

        row.innerHTML = `
            <td>${property.area_name || 'N/A'}</td>
            <td>${this.formatCurrency(property.price)}</td>
            <td>${property.bedrooms || 'N/A'}</td>
            <td>${property.bathrooms || 'N/A'}</td>
            <td>${property.land_size ? `${Math.round(property.land_size)} m²` : 'N/A'}</td>
            <td>${property.price_per_sqm ? this.formatCurrency(property.price_per_sqm) : 'N/A'}</td>
            <td>${property.listing_date.toLocaleDateString()}</td>
            <td>
                <button class="btn-primary view-details" data-index="${index}">View Details</button>
            </td>
        `;

        // Add click handler for view details
        row.querySelector('.view-details').addEventListener('click', (e) => {
            e.stopPropagation();
            this.showPropertyDetails(index);
        });

        return row;
    }

    showPropertyDetails(index) {
        const property = this.properties[index];
        const modal = document.getElementById('property-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');

        modalTitle.textContent = property.area_name || 'Property Details';

        const attrs = property.attributes || {};
        modalContent.innerHTML = `
            <div class="property-details">
                <div class="detail-section">
                    <h4>Property Information</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>Price:</strong> ${this.formatCurrency(property.price)}
                        </div>
                        <div class="detail-item">
                            <strong>Property Type:</strong> ${property.property_type}
                        </div>
                        <div class="detail-item">
                            <strong>Bedrooms:</strong> ${attrs.bedrooms || 'N/A'}
                        </div>
                        <div class="detail-item">
                            <strong>Bathrooms:</strong> ${attrs.bathrooms || 'N/A'}
                        </div>
                        <div class="detail-item">
                            <strong>Garage Spaces:</strong> ${attrs.garage_spaces || 'N/A'}
                        </div>
                        <div class="detail-item">
                            <strong>Land Size:</strong> ${property.land_size ? `${Math.round(property.land_size)} m²` : 'N/A'}
                        </div>
                        <div class="detail-item">
                            <strong>Price per m²:</strong> ${property.price_per_sqm ? this.formatCurrency(property.price_per_sqm) : 'N/A'}
                        </div>
                        <div class="detail-item">
                            <strong>Listed:</strong> ${property.listing_date.toLocaleDateString()}
                        </div>
                    </div>
                </div>

                ${attrs.description ? `
                <div class="detail-section">
                    <h4>Description</h4>
                    <p class="property-description">${attrs.description}</p>
                </div>
                ` : ''}

                <div class="detail-section">
                    <h4>Location</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>Address:</strong> ${property.area_name}
                        </div>
                        <div class="detail-item">
                            <strong>Coordinates:</strong> ${property.coordinates.latitude.toFixed(6)}, ${property.coordinates.longitude.toFixed(6)}
                        </div>
                    </div>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
    }

    sortTable(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortDirection = 'asc';
        }
        this.sortColumn = column;

        this.properties.sort((a, b) => {
            let aVal = a[column];
            let bVal = b[column];

            // Handle null values
            if (aVal === null || aVal === undefined) aVal = '';
            if (bVal === null || bVal === undefined) bVal = '';

            // Convert to numbers for numeric columns
            if (['price', 'bedrooms', 'bathrooms', 'land_size', 'price_per_sqm'].includes(column)) {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            }

            // Convert to dates for date columns
            if (column === 'listing_date') {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            }

            if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        this.renderPropertiesTable();
        this.updateSortIndicators();
    }

    updateSortIndicators() {
        document.querySelectorAll('th i').forEach(indicator => {
            indicator.className = 'fas fa-sort';
        });

        if (this.sortColumn) {
            const activeIndicator = document.querySelector(`th[data-sort="${this.sortColumn}"] i`);
            if (activeIndicator) {
                activeIndicator.className = this.sortDirection === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
            }
        }
    }

    expandAllRows() {
        // Implementation for expanding all rows if needed
        console.log('Expand all rows');
    }

    collapseAllRows() {
        // Implementation for collapsing all rows if needed
        console.log('Collapse all rows');
    }

    closeModal() {
        document.getElementById('property-modal').classList.add('hidden');
    }

    showSections() {
        // Show all sections with new data
        document.getElementById('stats-section').classList.remove('hidden');
        document.getElementById('charts-section').classList.remove('hidden');
        document.getElementById('properties-section').classList.remove('hidden');
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (show) {
            loading.classList.remove('hidden');
        } else {
            loading.classList.add('hidden');
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        errorText.textContent = message;
        errorDiv.classList.remove('hidden');
    }

    hideError() {
        document.getElementById('error-message').classList.add('hidden');
    }

    // Utility functions
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-AU', {
            style: 'currency',
            currency: 'AUD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    average(arr) {
        return arr.reduce((sum, val) => sum + val, 0) / arr.length;
    }

    median(arr) {
        const sorted = [...arr].sort((a, b) => a - b);
        const mid = Math.floor(sorted.length / 2);
        return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new PropertyDashboard();
});