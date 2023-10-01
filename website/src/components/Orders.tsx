import { useEffect, useState } from 'react';
import './Orders.css';
import { API_URL } from '../helper/Constants';

function OrdersTable() {
    const [orders, setOrders] = useState([]);

    useEffect(() => {
        const intervalId = setInterval(() => {
            fetch(`http://${API_URL}/orders`, {
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
            .then(data => setOrders(data))
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
                {orders.map(order => (
                    <tr key={order.id}>
                        {headers.map(header => (
                            <td key={header}>{order[header]}</td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

export default OrdersTable