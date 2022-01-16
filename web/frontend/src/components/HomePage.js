import React, { Component } from 'react';
import AboutPage from "./AboutPage";
import Button from "@material-ui/core/Button";
import Grid from "@material-ui/core/Grid";
import Typography from "@material-ui/core/Typography";
import TextField from  "@material-ui/core/TextField";
import FormControl from "@material-ui/core/FormControl";
import FormHelperText from "@material-ui/core/FormHelperText";
import { MenuItems } from "./MenuItems";
import './HomePage.css';
import { 
	BrowserRouter as Router, 
	Switch, 
	Route, 
	Link, 
	Redirect 
} from "react-router-dom";
import Drop from './Drop'

export default class HomePage extends Component {
	defaultMotionDirection = 90;

	constructor(props) {
		super(props);
	}
	
	render() {
		return (
			<Grid container spacing={1}>
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
				<Grid item xs={12} align='center'>
					<Typography component='h5' variant='h5'>
						Upload your track and DJ-MVP will produce a music video for you
					</Typography>
				</Grid>
				<Grid item xs={12} align="center">
					<div align='center'>
						Music Video Producer
					</div>
				</Grid>
				<div className = "drop">
	                <Grid item>
	                    <Drop/>
	                </Grid>
                </div>
			</Grid>
		);
	}
}
