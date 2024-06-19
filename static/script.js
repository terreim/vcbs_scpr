let allStocks = [];

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search');
    const stockTableBody = document.querySelector('#stock-table tbody');
    const connectButton = document.getElementById('connect');

    let socket = null;

    function fetchStocksAndUpdateTable() {
        fetch('/api/data')
            .then(response => response.json())
            .then(stocks => {
                console.log("Fetched Stocks:", stocks);
                allStocks = stocks; 
                displayStockTable(stocks);
            })
            .catch(error => console.error('Failed to fetch stocks:', error));
    }

    function displayStockTable(stocks) {
        stockTableBody.innerHTML = '';

        stocks.forEach((stock) => {
            let changeClass;
            if (stock.change.includes('+')) {
                changeClass = 'positive';
            } else if (stock.change.includes('-')) {
                changeClass = 'negative';
            } else {
                changeClass = 'neutral';
            }

            const tr = document.createElement('tr');
            
            // Setup the row's HTML content
            tr.innerHTML = `
                <td>${stock.name}</td>
                <td>${stock.ceiling}</td>
                <td>${stock.floor}</td>
                <td>${stock.prior_close_price}</td>
                <td>${stock.p3_best_bid}</td>
                <td>${stock.p3_best_bid_vol}</td>
                <td>${stock.p2_best_bid}</td>
                <td>${stock.p2_best_bid_vol}</td>
                <td>${stock.p1_best_bid}</td>
                <td>${stock.p1_best_bid_vol}</td>
                <td class="${changeClass}">${stock.change}</td>
                <td>${stock.close_price}</td>  
                <td>${stock.close_volume}</td>
                <td>${stock.p1_best_ask}</td>  
                <td>${stock.p1_best_ask_vol}</td>
                <td>${stock.p2_best_ask}</td>
                <td>${stock.p2_best_ask_vol}</td>
                <td>${stock.p3_best_ask}</td> 
                <td>${stock.p3_best_ask_vol}</td> 
                <td>${stock.total_trading}</td>  
                <td>${stock.open}</td>
                <td>${stock.high}</td>
                <td>${stock.low}</td>
                <td>${stock.foreign_buy}</td> 
                <td>${stock.foreign_sell}</td>
                <td>${stock.foreign_remain}</td>
            `;

            stockTableBody.appendChild(tr);
        });
    }

    searchInput.addEventListener('input', (event) => {
        const searchTerm = event.target.value.toLowerCase();
        const filteredStocks = allStocks.filter(stock => 
            stock.name.toLowerCase().includes(searchTerm));
        displayStockTable(filteredStocks); 
    });

    connectButton.addEventListener('click', () => {
        if (!socket) {
            socket = io('vcbs-scpr-76640d9fe868.herokuapp.com', {
                transports: ['websocket', 'polling'],
                reconnectionAttempts: 5,
                timeout: 60000,
                upgrade: true
            });

            socket.on('connect', () => {
                console.log('Connected to server');
                fetchStocksAndUpdateTable();
            });

            socket.on('connect_error', (error) => {
                console.log('Connection Error:', error);
            });

            socket.on('disconnect', (reason) => {
                console.log('Disconnected:', reason);
            });

            socket.on('update_data', (stocks) => {
                console.log("Real-time update received:", stocks);
                allStocks = stocks;
                displayStockTable(stocks);
            });
        }
    });

    window.setInterval(fetchStocksAndUpdateTable, 3000);
});
