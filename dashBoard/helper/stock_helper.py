import dash_bootstrap_components as dbc
import dash_html_components as html
from helper.helperFunctions import helper_functions
from rich.console import Console

console = Console()


def get_stock_data_in_form_of_table():
    helpers = helper_functions()

    my_stocks_json = helpers.stock_order
    # print(my_stocks_json)

    stocks_dic = helpers.get_all_stock_dic()
    """
{
    "WIPRO": [
        10, unit
        4094.0 total invested
    ]
}
    """
    table = []

    for k, v in my_stocks_json.items():
        total_invested = v[1]
        quote = {
            "closePrice": round(total_invested / v[0], 2),
            "previousClose": round(total_invested / v[0], 2),
        }

        current_price = float(quote["closePrice"])
        previous_close = float(quote["previousClose"])

        day_change = current_price - previous_close
        day_change_percentage = (
            round(day_change / previous_close * 100, 2) if previous_close != 0 else 0
        )
        total_returns = v[0] * current_price
        table.append(
            {
                "name": stocks_dic[k],
                "units": v[0],
                "average_price": round(total_invested / v[0], 2),
                "market_price": current_price,
                "day_change": day_change,
                "day_change_percentage": day_change_percentage,
                "total_invested": total_invested,
                "current": total_returns,
                "returns": total_returns - total_invested,
                "returns_percentage": round(
                    (total_returns - total_invested) / total_invested * 100, 2
                )
                if total_invested != 0
                else 0,
            }
        )

    table_data = [
        html.Tr(
            [
                html.Th("Name"),
                html.Th("Market Price"),
                html.Th("Returns %"),
                html.Th("Current"),
            ]
        )
    ]
    table_body = []
    for k in table:
        tr = html.Tr()
        tr.children = []
        _1st_td = html.Td(
            [
                k["name"],
                html.Br(),
                k["units"],
                " shares",
                " Avg ",
                "Rs ",
                k["average_price"],
            ]
        )
        _2nd_td = html.Td(
            [
                k["market_price"],
                html.Br(),
                k["day_change"],
                " (",
                k["day_change_percentage"],
                "%)",
            ]
        )
        _3rd_td = html.Td(
            [k["returns"], html.Br(), " (", k["returns_percentage"], "%)"]
        )
        _4th_td = html.Td([k["current"], html.Br(), k["total_invested"]])
        tr.children = [_1st_td, _2nd_td, _3rd_td, _4th_td]
        table_body.append(tr)

    table_data.append(html.Tbody(table_body))

    return dbc.Table(
        table_data,
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        className="table table-hover table-bordered table-striped  p-10 table-responsive-sm table-responsive-md "
                  "table-responsive-lg table-responsive-xl text-align-center",
        style={
            "margin-top": "100px",
            "margin-bottom": "10px",
            "text-align": "center",
        },
    )
