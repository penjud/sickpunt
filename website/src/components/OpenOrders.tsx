import { useEffect, useState } from 'react';
import './Orders.css';
import { API_URL } from '../helper/Constants';


function OpenOrders() {  // Renamed component to OpenOrders
    const [orders, setOrders] = useState([]);

    useEffect(() => {
        const intervalId = setInterval(() => {
            fetch(`http://${API_URL}/open_orders`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Add other headers here if necessary
                },
                // Uncomment the line below and adjust the body data if you need to send a payload with the POST request
                // body: JSON.stringify({ key: 'value' }),
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => setOrders(data.orders))  // Assuming the new endpoint returns an object with an orders property
            .catch(error => {
                // Handle the error here. Maybe set an error state, or use a console.log.
                console.error('Error fetching orders:', error);
            });
        }, 1000);
    
        return () => clearInterval(intervalId);
    }, []);

    const headers = orders.length > 0 ? Object.keys(orders[0]) : [];

    return (
        <table>
            <thead>
                <tr>
                    {headers.map(header => (
                        <th key={header}>{header}</th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {orders.map((order, index) => (  // Updated key to index since order.id may not exist
                    <tr key={index}>
                        {headers.map(header => (
                            <td key={header}>{order[header]}</td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

export default OpenOrders;  // Updated export to OpenOrders
