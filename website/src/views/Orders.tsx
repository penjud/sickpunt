import 'bootstrap/dist/css/bootstrap.css';
import OpenOrders from '../components/OpenOrders';
import OrdersTable from '../components/Orders';

function Orders() {
  return (
    <>
      <div className="h2 mt-4 mb-4"> Open Orders</div>
      <OpenOrders />
      
      <div className="h2 mt-4 mb-4"> Placed Orders</div>
      <OrdersTable />

    </>
  )
}

export default Orders