import React, { useEffect, useState } from 'react';
import {
  Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TablePagination, Paper, TextField, Button, MenuItem, FormControl, InputLabel,
  Select, IconButton, Typography, useMediaQuery
} from '@mui/material';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import DoneIcon from '@mui/icons-material/Done';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import CheckIcon from '@mui/icons-material/Check';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import api from '../api/axios';
import { jwtDecode } from 'jwt-decode';
import AddTaskModal from '../modals/AddTaskModal';

dayjs.extend(utc);

const TaskTable = ({ isBackdatedTab = false }) => {
  const [tasks, setTasks] = useState([]);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const isMobile = useMediaQuery('(max-width:768px)');

  const [fromDate, setFromDate] = useState(dayjs().subtract(7, 'day'));
  const [toDate, setToDate] = useState(dayjs());
  const [filters, setFilters] = useState({});
  const [pendingFilters, setPendingFilters] = useState({});
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [sortConfig, setSortConfig] = useState({ key: 'start_time', direction: 'desc' });

  const [editTask, setEditTask] = useState(null);

  const token = localStorage.getItem('token');
  const currentUser = token ? (() => {
    try {
      const decoded = jwtDecode(token);
      return { role: decoded.role, id: parseInt(decoded.sub) };
    } catch {
      return { role: '', id: null };
    }
  })() : { role: '', id: null };

  useEffect(() => {
    const defaultFilters = {
      task_type: '',
      status: isBackdatedTab ? 'To Be Approved' : '',
      project_id: '',
      user_id: currentUser.role === 'Employee' ? currentUser.id : null,
      created_by: null,
      only_backdated: isBackdatedTab,
      filter_backdated_by_creator_type: 'all'
    };
    setFilters(defaultFilters);
    setPendingFilters(defaultFilters);
    setPage(0);
  }, [isBackdatedTab]);

  const fetchProjects = async () => {
    try {
      const res = await api.get('/projects/');
      setProjects(res.data);
    } catch (error) {
      console.error('Failed to fetch projects', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await api.get('/users/get-users');
      setUsers(res.data);
    } catch (error) {
      console.error('Failed to fetch users', error);
    }
  };

  const fetchTasks = async () => {
    const payload = {
      ...filters,
      from_date: fromDate.utc().format('YYYY-MM-DD'),
      to_date: toDate.utc().format('YYYY-MM-DD')
    };

    Object.keys(payload).forEach((key) => {
      if (payload[key] === '' || payload[key] === undefined) {
        payload[key] = null;
      }
    });

    try {
      const res = await api.post(`/tasks?page=${page + 1}&page_size=${rowsPerPage}&search=${search}`, payload);
      const sorted = clientSort(res.data, sortConfig);
      setTasks(sorted);
    } catch (error) {
      console.error('Failed to fetch tasks', error);
    }
  };

  const clientSort = (data, config) => {
    return [...data].sort((a, b) => {
      const aVal = a[config.key];
      const bVal = b[config.key];
      if (aVal < bVal) return config.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return config.direction === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleApplyFilters = () => {
    setFilters({ ...pendingFilters });
    setPage(0);
  };

  const handleComplete = async (id) => {
    try {
      await api.put(`/tasks/${id}/complete`);
      fetchTasks();
    } catch (err) {
      console.error('Failed to complete task', err);
    }
  };

  const handleApprove = async (id) => {
    try {
      await api.put(`/tasks/${id}/approve`);
      fetchTasks();
    } catch (err) {
      console.error('Failed to approve task', err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/tasks/${id}`);
      fetchTasks();
    } catch (err) {
      console.error('Failed to delete task', err);
    }
  };

  const handleDownload = async () => {
    const payload = {
      ...filters,
      from_date: fromDate.utc().format('YYYY-MM-DD'),
      to_date: toDate.utc().format('YYYY-MM-DD')
    };

    Object.keys(payload).forEach(key => {
      if (payload[key] === '' || payload[key] === undefined) {
        payload[key] = null;
      }
    });

    try {
      const res = await api.post(`/tasks/download`, payload, {
        responseType: 'blob',
      });

      const blob = new Blob([res.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'task_report.xlsx');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Failed to download report', error);
    }
  };

  useEffect(() => {
    fetchProjects();
    if (currentUser.role !== 'Employee') fetchUsers();
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [filters, page, rowsPerPage, fromDate, toDate, sortConfig]);

  const headers = [
    { key: 'date', label: 'Date' },
    { key: 'user_id', label: 'User' },
    { key: 'project_id', label: 'Project' },
    { key: 'task_details', label: 'Task Details' },
    { key: 'start_time', label: 'Start' },
    { key: 'end_time', label: 'End' },
    { key: 'task_type', label: 'Type' },
    { key: 'reviewer_id', label: 'Reviewer' },
    { key: 'status', label: 'Status' },
    { key: 'total_time_minutes', label: 'Total (min)' }
  ];

  return (
    <Box mt={2}>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" flexWrap="wrap" gap={2}>
          <TextField size="small" label="Search" value={search} onChange={(e) => setSearch(e.target.value)} />
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker label="From Date" value={fromDate} onChange={setFromDate} />
            <DatePicker label="To Date" value={toDate} onChange={setToDate} />
          </LocalizationProvider>

          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Project</InputLabel>
            <Select name="project_id" value={pendingFilters.project_id || ''} onChange={(e) => setPendingFilters({ ...pendingFilters, project_id: e.target.value })}>
              <MenuItem value="">All</MenuItem>
              {projects.map(p => <MenuItem key={p.id} value={p.id}>{p.project_name}</MenuItem>)}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Status</InputLabel>
            <Select name="status" value={pendingFilters.status || ''} onChange={(e) => setPendingFilters({ ...pendingFilters, status: e.target.value })}>
              <MenuItem value="">All</MenuItem>
              {["In Progress", "To Be Approved", "Approved", "Done"].map(status => (
                <MenuItem key={status} value={status}>{status}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Backdated By</InputLabel>
            <Select name="filter_backdated_by_creator_type" value={pendingFilters.filter_backdated_by_creator_type || ''} onChange={(e) => setPendingFilters({ ...pendingFilters, filter_backdated_by_creator_type: e.target.value })}>
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="own">Own</MenuItem>
              <MenuItem value="manager">Manager</MenuItem>
            </Select>
          </FormControl>

          {currentUser.role !== 'Employee' && (
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>User</InputLabel>
              <Select name="user_id" value={pendingFilters.user_id || ''} onChange={(e) => setPendingFilters({ ...pendingFilters, user_id: e.target.value })}>
                <MenuItem value="">All</MenuItem>
                {users.map(u => <MenuItem key={u.id} value={u.id}>{u.name}</MenuItem>)}
              </Select>
            </FormControl>
          )}

          <Button variant="contained" onClick={handleApplyFilters}>Apply Filters</Button>
          <Button variant="outlined" onClick={handleDownload}>Download Report</Button>
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {headers.map(header => (
                <TableCell key={header.key} onClick={() => handleSort(header.key)} sx={{ cursor: 'pointer' }}>
                  {header.label}
                  {sortConfig.key === header.key && (
                    sortConfig.direction === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </TableCell>
              ))}
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.length === 0 ? (
              <TableRow>
                <TableCell colSpan={headers.length + 1}>
                  <Typography align="center" color="textSecondary">No data found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              tasks.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map(task => (
                <TableRow key={task.id}>
                  <TableCell>{task.date}</TableCell>
                  <TableCell>{users.find(u => u.id === task.user_id)?.name || '-'}</TableCell>
                  <TableCell>{projects.find(p => p.id === task.project_id)?.project_name || '-'}</TableCell>
                  <TableCell>{task.task_details}</TableCell>
                  <TableCell>{new Date(task.start_time).toLocaleString()}</TableCell>
                  <TableCell>{task.end_time ? new Date(task.end_time).toLocaleString() : '-'}</TableCell>
                  <TableCell>{task.task_type}</TableCell>
                  <TableCell>{users.find(u => u.id === task.reviewer_id)?.name || '-'}</TableCell>
                  <TableCell>{task.status}</TableCell>
                  <TableCell>{task.total_time_minutes ?? '-'}</TableCell>
                  <TableCell>
                    {task.status === 'In Progress' && task.user_id === currentUser.id && (
                      <IconButton onClick={() => handleComplete(task.id)}><DoneIcon /></IconButton>
                    )}
                    {task.status === 'To Be Approved' &&
                      ['Manager', 'Management', 'Admin'].includes(currentUser.role) &&
                      isBackdatedTab && (
                        <IconButton onClick={() => handleApprove(task.id)}><CheckIcon /></IconButton>
                    )}
                    {['Manager', 'Management', 'Admin'].includes(currentUser.role) &&
                      task.status !== 'Approved' &&
                      task.status !== 'Done' && (
                        <IconButton onClick={() => setEditTask(task)}><EditIcon /></IconButton>
                    )}
                    <IconButton onClick={() => handleDelete(task.id)}><DeleteIcon /></IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={tasks.length}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value)); setPage(0); }}
        />
      </TableContainer>

      {/* Reuse AddTaskModal for editing */}
      {editTask && (
        <AddTaskModal
          open={Boolean(editTask)}
          handleClose={() => setEditTask(null)}
          onTaskAdded={fetchTasks}
          isBackdated={editTask.is_backdated}
          editTaskData={editTask}
          isEdit={true}
        />
      )}
    </Box>
  );
};

export default TaskTable;
