import OpenOrders from '../components/OpenOrders'
import OrdersTable from '../components/Orders'
import 'bootstrap/dist/css/bootstrap.css';

function Orders() {
  return (
    <>
      <div className="h2 mt-4 mb-4"> Placed Orders</div>
      <OrdersTable />

      <div className="h2 mt-4 mb-4"> Open Orders</div>
      <OpenOrders />
    </>
  )
}

export default Orders