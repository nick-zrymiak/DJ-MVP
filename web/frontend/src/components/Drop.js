import React, {useMemo} from 'react';
import {useDropzone} from 'react-dropzone';
import Button from '@material-ui/core/Button';
import Box from '@material-ui/core/Box';
import TextField from '@material-ui/core/TextField';
import axios from 'axios';

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

export default function Drop() {
	const handleSubmit = (e) => {
	    e.preventDefault();
	
	    const data = new FormData(e.currentTarget)
	
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
		<div {...getRootProps({style})}>
		  <input {...getInputProps()} name='audio'/>
		  <p>Drag 'n' drop some files here</p>
		  <button type="button" onClick={open}>
		    Open File Dialog
		  </button>
		</div>
		<aside>
		  <h4>Files</h4>
		  <ul>{files}</ul>
		</aside>
		<TextField
            id="mirror"
            label="Mirror"
            variant="outlined"
            margin="normal"
            fullWidth
            name="mirror"
        />
		<Button
		    type="submit"
		    fullWidth
		    variant="contained"
		    sx={{ mt: 4, mb: 2 }}
		 >
		    GENERATE FULL VIDEO
		 </Button>
	</Box>
	</div>
  );
}
