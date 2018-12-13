
export function setSidebarShown(sidebarShown) {
  return {
    type: "SET_SIDEBAR_SHOWN",
    payload: sidebarShown
  };
}


export function setSidebarSectionId(sectionId) {
  return {
    type: "SET_SIDEBAR_SECTIONID",
    payload: sectionId
  };
}

export function setAccountMenuShown(accountMenuShown) {
  return {
    type: "SET_ACCOUNTMENU_SHOWN",
    payload: accountMenuShown
  };
}


export function setHeaderCollapsed(headerCollapsed) {
  return {
    type: "SET_HEADER_COLLAPSED",
    payload: headerCollapsed
  };
}

