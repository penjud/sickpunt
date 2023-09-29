import OrdersTable from '../components/Orders'

function Home() {
  return (
    <>
      <div className="h2"> Placed Orders</div>
      <OrdersTable />
    </>
  )
}

export default Home