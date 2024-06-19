document.addEventListener('DOMContentLoaded', () => {
    let allStocks = [];
    const searchInput = document.getElementById('search');
    const stockTableBody = document.querySelector('#stock-table tbody');

    // Connect to the Socket.IO server
    const socket = io('vcbs-scpr-76640d9fe868.herokuapp.com', {
        transports: ['websocket', 'polling'],
        reconnectionAttempts: 5,
        timeout: 60000,
        upgrade: true
    });

    // Fetch stocks from the server and update the table
    function fetchStocksAndUpdateTable() {
        fetch('/api/data')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(stocks => {
                console.log("Fetched Stocks:", stocks);
                allStocks = stocks; 
                displayStockTable(stocks);
            })
            .catch(error => console.error('Failed to fetch stocks:', error));
    }

    // Display the stock data in the table
    function displayStockTable(stocks) {
        stockTableBody.innerHTML = '';

        stocks.forEach((stock) => {
            let changeClass = 'neutral';
            if (stock.change.includes('+')) {
                changeClass = 'positive';
            } else if (stock.change.includes('-')) {
                changeClass = 'negative';
            }

            const tr = document.createElement('tr');
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

    // Filter stocks based on the search input
    searchInput.addEventListener('input', (event) => {
        const searchTerm = event.target.value.toLowerCase();
        const filteredStocks = allStocks.filter(stock => 
            stock.name.toLowerCase().includes(searchTerm));
        displayStockTable(filteredStocks); 
    });

    // Socket.IO event handlers
    socket.on('connect', () => {
        console.log('Connected to server');
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

    // Fetch initial stock data when the page loads
    fetchStocksAndUpdateTable();
});
