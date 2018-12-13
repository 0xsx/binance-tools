import expect from "expect"

const defaultState = {
  latency: 0,
  serverTime: 0,
  connectTime: 0,
  connectionStatus: "NOT_CONNECTED",
  fatalError: false,
  errorMsg: ""
};



export default function reducer(state=defaultState, action) {
  
  switch (action.type) {

    case "SET_LATENCY": {
      return {...state, latency: action.payload}
    }

    case "SET_SERVER_TIME": {
      return {...state, serverTime: action.payload}
    }

    case "SET_CONNECT_TIME": {
      return {...state, connectTime: action.payload}
    }

    case "SET_CONNECTION_STATUS": {
      return {...state, connectionStatus: action.payload}
    }

    case "SET_FATAL_ERROR": {
      return {...state, fatalError: action.payload}
    }

    case "SET_ERROR_MSG": {
      return {...state, errorMsg: action.payload}
    }

    default: {
      return state;
    }

  }

}

