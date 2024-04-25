import streamlit as st
import pandas as pd
import numpy as np 

def main():
    st.title("Invoice Comparison Report")

    st.write("### Upload CSV File 1 - dhl Orders")
    dhl_orders = st.file_uploader("dhl Orders upload", type=['csv'])
    if dhl_orders:
        if st.button('Process File 1'):
            processed_dhl_orders = process_data(dhl_orders)
            st.subheader("process dhl Orders")
            st.write(processed_dhl_orders)

def process_data(uploaded_file):
    # Define column names based on Excel column indices
    column_names = {
        5: 'orderId',
        11: 'trackingNum1',
        12: 'trackingNumber',
        14: 'address1',
        16: 'city',
        17: 'state',
        18: 'postalCode',
        19: 'country',
        21: 'shippingMethod',
        24: 'weight',
        25: 'weight_unit',
        28: 'pricingZone',
        29: 'dhlPrice',
        30: 'orderId_misplaced',
        64: 'surCharge'
        # Add more column names as needed
    }
    updated_dhl_orders = pd.read_csv(uploaded_file, skiprows=1, header=None, usecols=column_names.keys(), names=column_names.values())
    print('before: ', updated_dhl_orders.head(20))
    print('before: ', updated_dhl_orders.info())
    print('before: ', updated_dhl_orders.shape)
    # REMOVE EMPTY ROWS if weight_unit is blank
    updated_dhl_orders.dropna(subset=['weight_unit'], inplace=True)
    print(updated_dhl_orders.shape)
    # IF ORDERID column is blank fill with orderId_misplaced column
    updated_dhl_orders['orderId'].fillna(updated_dhl_orders['orderId_misplaced'], inplace=True)
    #DROP orderId_misplaced column
    updated_dhl_orders.drop(columns=['orderId_misplaced'], inplace=True)
    # if weigh_unit column is equal to "LB" then move values from trackingNum1 column to TrackingNumber column
    updated_dhl_orders['trackingNumber'] = np.where(updated_dhl_orders['weight_unit'] == 'LB', 
                                               updated_dhl_orders['trackingNum1'], 
                                               updated_dhl_orders['trackingNumber'])
    # Make a totalPrice Column: Add dhlPrice + surCharge
    updated_dhl_orders['total_price'] = np.round((updated_dhl_orders['dhlPrice']+updated_dhl_orders['surCharge']),2)
    # CREATE A dhlMarkup(11%): TotalPrice * 1.11
    updated_dhl_orders['dhlMarkup(11%)'] = updated_dhl_orders['total_price']*1.11
    # Create a finalWeight Column: If weight_unit = "LB" then leave as is, if not convert Oz --> Lbs
    updated_dhl_orders['finalWeight'] = np.where(updated_dhl_orders['weight_unit'] == 'OZ', updated_dhl_orders['weight']/16, updated_dhl_orders['weight'])
    # REMOVE WEIGHT AND WEIGHT_UNIT columns
    updated_dhl_orders.drop(columns=['weight', 'weight_unit','trackingNum1'], inplace=True)
    print('after: ', updated_dhl_orders.head(20))
    print('after: ', updated_dhl_orders.info())
    print('after: ', updated_dhl_orders.shape)
    return updated_dhl_orders


if __name__ == "__main__":
    main()