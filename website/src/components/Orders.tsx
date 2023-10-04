import { useEffect, useState } from 'react';
import './Orders.css';
import { API_URL } from '../helper/Constants';
import axios from 'axios';
import CircularProgress from '@mui/material/CircularProgress';  // <-- Import this

function OrdersTable() {
    const [orders, setOrders] = useState([]);
    const [isLoading, setIsLoading] = useState(true);  // <-- Add this line

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
                setIsLoading(false);  // <-- Set loading to false when data is received
            })
            .catch(error => {
                console.error('Error fetching orders:', error);
            });
        }, 10000);
    
        return () => clearInterval(intervalId);
    }, []);

    const headers = orders.length > 0 ? Object.keys(orders[0]) : [];

    return (
        <div>
            {isLoading ? (  // <-- Conditional rendering for loading state
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
            <CircularProgress />
          </div>
            ) : (
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
            )}
        </div>
    );
}

export default OrdersTable;
