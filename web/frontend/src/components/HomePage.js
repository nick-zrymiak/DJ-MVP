import React, { Component } from 'react';
import AboutPage from "./AboutPage";
import Button from "@material-ui/core/Button";
import Grid from "@material-ui/core/Grid";
import Typography from "@material-ui/core/Typography";
import TextField from  "@material-ui/core/TextField";
import { MenuItems } from "./MenuItems"
import './HomePage.css'
import { 
	BrowserRouter as Router, 
	Switch, 
	Route, 
	Link, 
	Redirect 
} from "react-router-dom";

export default class HomePage extends Component {
	defaultMotionDirection = 90;

	constructor(props) {
		super(props);
	}
	
	render() {
		return (
			<nav className="NavbarItems">
				<h1 className="navbar-logo">
					<img src={ require("../images/logo.jpeg").default } className="fab fa-react" />
				</h1>
				<ul className="nav-menu">
					{MenuItems.map((item, index) => {
						return (
							<li key={index}>
								<a className={item.cName} href={item.url}>
								{item.title}
								</a>
							</li>
						)
					})}
				</ul>
			</nav>
		);
	}
}
