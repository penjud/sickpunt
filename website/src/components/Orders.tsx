import { useEffect, useState } from 'react';
import './Orders.css';
import { API_URL } from '../helper/Constants';
import axios from 'axios';

function OrdersTable() {
    const [orders, setOrders] = useState([]);

    useEffect(() => {
        const intervalId = setInterval(() => {
            axios.post(`http://${API_URL}/orders`, 
                {
                    headers: {
                        'Content-Type': 'application/json',

                    },
                }
            )
            .then(response => {
                setOrders(response.data);
            })
            .catch(error => {
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