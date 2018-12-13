import React from "react";
import ReactDOM from "react-dom";
import {Provider} from "react-redux";
import {combineReducers, createStore} from "redux";



import AppMain from "./components/AppMain";

import layout from "./ar/layout-reducer";
import language from "./ar/language-reducer";
import status from "./ar/status-reducer";


const combinedReducer = combineReducers({
  layout,
  language,
  status
});

const store = createStore(combinedReducer);


ReactDOM.render(

  <Provider store={store}>
    <AppMain />
  </Provider>,

  document.getElementById("app"));

