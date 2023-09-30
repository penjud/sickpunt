import OpenOrders from '../components/OpenOrders'
import OrdersTable from '../components/Orders'

function Orders() {
  return (
    <>
      <div className="h2"> Placed Orders</div>
      <OrdersTable />

      <div className="h2"> Open Orders</div>
      <OpenOrders />
    </>
  )
}

export default Orders