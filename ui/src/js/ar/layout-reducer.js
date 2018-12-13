import expect from "expect"

const defaultState = {
  sidebarShown: false,
  sidebarSectionId: null,
  accountMenuShown: false
};



export default function reducer(state=defaultState, action) {
  
  switch (action.type) {

    case "SET_SIDEBAR_SHOWN": {
      return {...state, sidebarShown: action.payload}
    }

    case "SET_SIDEBAR_SECTIONID": {
      return {...state, sidebarSectionId: action.payload}
    }

    case "SET_ACCOUNTMENU_SHOWN": {
      return {...state, accountMenuShown: action.payload}
    }

    default: {
      return state;
    }

  }

}

