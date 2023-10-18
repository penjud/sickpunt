import 'bootstrap/dist/css/bootstrap.css';
import Table from '../components/Table';

function Orders() {
  return (
    <>
      <div className="h2 mt-4 mb-4"> Orders on betfair</div>
      <Table endpoint="open_orders"/>

      <div className="h2 mt-4 mb-4"> Bot triggered orders</div>
      <Table endpoint="orders"/>

    </>
  )
}

export default Orders