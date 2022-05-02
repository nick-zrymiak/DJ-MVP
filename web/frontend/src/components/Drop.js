import React, {useMemo} from 'react';
import {useDropzone} from 'react-dropzone';
import Button from '@material-ui/core/Button';
import Box from '@material-ui/core/Box';
import TextField from '@material-ui/core/TextField';
import {Slider} from "@material-ui/core";
import Checkbox from "@material-ui/core/Checkbox";
import {CompactPicker} from 'react-color'
import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";
import Grid from "@material-ui/core/Grid";
import axios from 'axios';
import './Drop.css';

const baseStyle = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: '20px',
  borderWidth: 2,
  borderRadius: 2,
  borderColor: '#eeeeee',
  borderStyle: 'dashed',
  backgroundColor: '#fafafa',
  color: '#bdbdbd',
  outline: 'none',
  transition: 'border .24s ease-in-out'
};

const activeStyle = {
  borderColor: '#2196f3'
};

const acceptStyle = {
  borderColor: '#00e676'
};

const rejectStyle = {
  borderColor: '#ff1744'
};

var fileDownload = require('js-file-download');

function motionDirectionValueText(motionDirectionValue) {
	return `${motionDirectionValue}°`;
}

function motionIntensityValueText(motionIntensityValue) {
	return `${motionIntensityValue}%`;
}


export default function Drop() {
	const [motionDirectionValue, setMotionDirectionValue] = React.useState([0, 360]);
	const [motionIntensityValue, setMotionIntensityValue] = React.useState([0, 100]);
	const [audioVideoAlignmentValue, setAudioVideoAlignmentValue] = React.useState(0);
	const [color, setColor] = React.useState('#fff')

	const handleSubmit = (e) => {
	    e.preventDefault();
	
	    const data = new FormData(e.currentTarget);
	
	    axios.post('http://127.0.0.1:8000/api/video', data).then (
	        result => {
	            console.log(result)
	            if (result['status'] == 200) {
					console.log('SUCCESSFUL POST')
					console.log(result.data)
					
					axios.get('http://127.0.0.1:8000/api/download', { 
			            responseType: 'blob',
			        }).then(res => {
			        	console.log('DOWNLOADING');
			        	video_name = result.data['audio'] 
			        	var i = video_name.lastIndexOf('/');
			        	var video_name = video_name.substring(i+1);
			        	video_name = video_name.substr(0, video_name.indexOf('.'));
			        	video_name = video_name.concat('.mp4');
			        	console.log
			            fileDownload(res.data, video_name);
			            console.log(res);
			        }).catch(err => {
			            console.log(err);
			        })
	            }
	
	        })
	        .catch(err => {
				console.log(err);
	        })
	};
	
	const {
	  getRootProps,
	  getInputProps,
	  isDragActive,
	  isDragAccept,
	  isDragReject,
	  acceptedFiles,
	  open
	} = useDropzone({accept: 'audio/*', noClick: true, noKeyboard: true});
	
	const style = useMemo(() => ({
	  ...baseStyle,
	  ...(isDragActive ? activeStyle : {}),
	  ...(isDragAccept ? acceptStyle : {}),
	  ...(isDragReject ? rejectStyle : {})
	}), [
	  isDragActive,
	  isDragReject,
	  isDragAccept
	]);
	
	const files = acceptedFiles.map(file => (
	  <li key={file.path}>
	  {file.path} - {file.size} bytes
	</li>
	));

  return (
    <div className="container">
    <Box
	    component="form"
	    noValidate
	    onSubmit={handleSubmit}
	    autoComplete="off"
	>
		<div className='drop-box'>
			<div className='drop-holder' {...getRootProps({style})}>
			  <input {...getInputProps()} name='audio'/>
			  <button className='drop-button' type="button" onClick={open}>
			    DROP YOUR AUDIO FILE HERE
			  </button>
			</div>
			<div className='file-holder'>
				<aside className='file'>
				  <h4 className='file-name'>File name</h4>
				  <ul className='file-name-size'>{files}</ul>
				</aside>
			</div>
			<div className='generate-ten-sec-video'>
				<Button
				    id='full_video'
				    name='full_video'
				    type="submit"
				    fullWidth
				    variant="contained"
				    sx={{ mt: 4, mb: 2 }}
				 >
				    GENERATE 10 SECOND VIDEO
				 </Button>
			</div>
			<div className='generate-full-video'>
				<Button
					id='ten_sec_video'
				    name='ten_sec_video'
				    type="submit"
				    fullWidth
				    variant="contained"
				    sx={{ mt: 4, mb: 2 }}
				 >
				    GENERATE FULL VIDEO
				 </Button>
			</div>
			<div className='progress-bar'>
				PROGRESS BAR
			</div>
		</div>
		<div className='settings'>
			<div className='segment-selection'>
				<h3 className='segment-selection-title'>Segment Selection</h3>
				<h4>Motion direction (&#176;)</h4>
				<div className='slider'>
					<Slider
						id='motion_direction'
						name='motion_direction'
						defaultValue={motionDirectionValue}
						getAriaValueText={motionDirectionValueText}
						valueLabelDisplay="auto"
						max={360}
					/>
				</div>
				<h4>Motion intensity (%)</h4>
				<div className='slider'>
					<Slider
						id='motion_intensity'
						name='motion_intensity'
						defaultValue={motionIntensityValue}
						getAriaValueText={motionIntensityValueText}
						valueLabelDisplay="auto"
					/>
				</div>
				<h4>Audio/video alignment (ms)</h4>
				<div className='slider'>
					<Slider
						id='audio_video_alignment'
						name='audio_video_alignment'
						valueLabelDisplay="auto"
						defaultValue={audioVideoAlignmentValue}
						min={-10}
						max={10}
					/>
				</div>
				<h4>Max repeated segments</h4>
				<div className='slider'>
					<Slider
						id='max_repeated_segments'
						name='max_repeated_segments'
						defaultValue={10}
						valueLabelDisplay="auto"
						min={10}
					/>
				</div>
				<h4>Max repeated songs</h4>
				<div className='slider'>
					<Slider
						id='max_repeated_songs'
						name='max_repeated_songs'
						defaultValue={10}
						valueLabelDisplay="auto"
						min={10}
					/>
				</div>
			</div>
			<div className='visual-effects'>
				<h3 className='visual-effects-title'>Visual Effects</h3>
					<Grid container spacing={2}>
						<div className='black-and-white-label'>
							<h4>Black and white</h4>
						</div>
						<div className='black-and-white'>
						</div>
						<div className='fade-label'>
							<h4>Fade</h4>
						</div>
						<div className='fade'>
						</div>
						<div className='mirror-label'>
							<h4>Mirror</h4>
						</div>
						<div className='mirror'>
						</div>
						<div className='datamosh-label'>
							<h4>Datamosh</h4>
						</div>
						<div className='datamosh'>
						</div>
						<div className='Paintify-label'>
							<h4>Paintify</h4>
						</div>
						<div className='paintify'>
						</div>
					</Grid>
			</div>
		</div>
	</Box>
	</div>
  );
}
