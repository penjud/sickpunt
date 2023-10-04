import { useEffect, useState } from 'react';
import './Orders.css';
import { API_URL } from '../helper/Constants';
import axios from 'axios';


function OpenOrders() {  // Renamed component to OpenOrders
    const [orders, setOrders] = useState([]);

    useEffect(() => {
        const intervalId = setInterval(() => {
            axios.post(`http://${API_URL}/open_orders`, 
                {
                    headers: {
                        'Content-Type': 'application/json',
                    },
                }
            )
            .then(response => {
                setOrders(response.data.orders); // Assuming the new endpoint returns an object with an "orders" property
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
