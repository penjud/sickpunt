import CircularProgress from '@mui/material/CircularProgress';
import axios from 'axios';
import { useEffect, useState } from 'react';
import { API_URL } from '../helper/Constants';
import './Orders.css';

function OrdersTable() {
    const [orders, setOrders] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [sortKey, setSortKey] = useState('timestamp');  // <-- Add this line for sorting
    const [isSortAscending, setIsSortAscending] = useState(false); // <-- Add this line for sorting direction
    const [filter, setFilter] = useState('');  // <-- Add this line for filtering
    const [isManuallySorted, setIsManuallySorted] = useState(false);

    useEffect(() => {
        axios.post(`http://${API_URL}/orders`,
            {
                headers: {
                    'Content-Type': 'application/json',
                },
            }
        )
        .then(response => {
            const sortedData = response.data.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
            setOrders(sortedData);
            setIsLoading(false);
        })
        .catch(error => {
            console.error('Error fetching orders:', error);
        });
    }, [isManuallySorted]);


    const handleSort = (key) => {
        setIsManuallySorted(true);
        const sortedData = [...orders].sort((a, b) => {
            const valA = key === 'timestamp' ? new Date(a[key]).toISOString() : a[key];
            const valB = key === 'timestamp' ? new Date(b[key]).toISOString() : b[key];
      
            if (valA < valB) return isSortAscending ? -1 : 1;
            if (valA > valB) return isSortAscending ? 1 : -1;
            return 0;
        });
    
        setOrders(sortedData);
        setSortKey(key);
        setIsSortAscending(!isSortAscending);
    };
    

    const filteredOrders = orders.filter(order => {
        return Object.values(order).some(value =>
            String(value).toLowerCase().includes(filter.toLowerCase())
        );
    });

    const headers = orders.length > 0 ? Object.keys(orders[0]) : [];

    return (
        <div>
            {isLoading ? (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
                    <CircularProgress />
                </div>
            ) : (
                <div>
                    <input type="text" placeholder="Filter..." onChange={(e) => setFilter(e.target.value)} />
                    <table>
                        <thead>
                            <tr>
                                {headers.map(header => (
                                    <th key={header} onClick={() => handleSort(header)}>
                                        {header}
                                        {sortKey === header && (isSortAscending ? ' ↓': ' ↑' )}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filteredOrders.map(order => (
                                <tr key={order.id}>
                                    {headers.map(header => (
                                        <td key={header}>{order[header]}</td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

export default OrdersTable;
