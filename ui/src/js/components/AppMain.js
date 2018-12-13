import React from "react";
import {connect} from "react-redux";





@connect((store) => {
  return {
    strings: store.language.strings,
    serverTime: store.status.serverTime,
    fatalError: store.status.fatalError,
    errorMsg: store.status.errorMsg,
    latency: store.status.latency,
    connectionStatus: store.status.connectionStatus,
  };
})
class AppMain extends React.Component {

  constructor(props, context) {
    super(props, context);

    this.state = {
      socketRunning: false
    };
  }


  reconnectSocket() {
    this.connection = new WebSocket("ws://" + window.location.hostname
                                    + ":" + window.location.port + "/socket");
    this.connection.onmessage = evt => {this.props.dispatch(JSON.parse(evt.data));};
    this.connection.onopen = evt => {this.setState({socketRunning: true});};
    this.connection.onclose = evt => {this.setState({socketRunning: false});};
    this.connection.onerror = evt => {this.setState({socketRunning: false});};
  }


  componentDidMount() {
    document.title = this.props.strings["name"];
    this.reconnectSocket();

    setInterval( () =>{
      if (!this.state.socketRunning) {
        this.reconnectSocket();
      }
    }, 2000);
  }




  render() {
    if (!this.state.socketRunning) {
      if (this.props.fatalError){
        return (
          <div>
            <h2>{this.props.strings["fatalError"]}</h2>
            <pre>{this.props.errorMsg}</pre>
          </div>
        );
      }
      return (
        <div>{this.props.strings["notRunning"]}</div>
      );
    }
    return (
      <div>
      {this.props.serverTime}<br />
      {this.props.latency}<br />
      {this.props.connectionStatus}<br />
      </div>
    );
  }


}

export default AppMain;

