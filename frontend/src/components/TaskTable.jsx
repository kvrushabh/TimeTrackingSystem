import React, { useEffect, useState } from 'react';
import {
  Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TablePagination, Paper, TextField, Button, MenuItem, FormControl, InputLabel,
  Select, IconButton, Typography, useMediaQuery, Tooltip, Dialog, DialogActions,
  DialogContent, DialogContentText, DialogTitle
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
  const [fromDate, setFromDate] = useState(dayjs().subtract(7, 'day'));
  const [toDate, setToDate] = useState(dayjs());
  const [filters, setFilters] = useState({});
  const [pendingFilters, setPendingFilters] = useState({});
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [sortConfig, setSortConfig] = useState({ key: 'start_time', direction: 'desc' });
  const [editTask, setEditTask] = useState(null);
  const [dialog, setDialog] = useState({ open: false, action: null, taskId: null });

  const token = localStorage.getItem('token');
  const currentUser = token ? (() => {
    try {
      const decoded = jwtDecode(token);
      return { role: decoded.role, id: parseInt(decoded.sub) };
    } catch {
      return { role: '', id: null };
    }
  })() : { role: '', id: null };

  const statusOptions = isBackdatedTab
    ? ["To Be Approved", "Approved"]
    : ["In Progress", "Done", "Approved"];

  const headers = [
    { key: 'date', label: 'Date' },
    { key: 'project_id', label: 'Project' },
    { key: 'user_id', label: 'User' },
    { key: 'task_title', label: 'Task Title' },
    { key: 'start_time', label: 'Start Time' },
    { key: 'end_time', label: 'End Time' },
    { key: 'total_time_minutes', label: 'Total Time' },
    { key: 'status', label: 'Status' },
  ];

  useEffect(() => {
    const defaultFilters = {
      task_type: '',
      status: isBackdatedTab ? 'To Be Approved' : '',
      project_id: '',
      user_id: currentUser.role === 'Employee' ? currentUser.id : null,
      created_by: null,
      only_backdated: isBackdatedTab,
      filter_backdated_by_creator_type: isBackdatedTab ? 'all' :''
    };
    setFilters(defaultFilters);
    setPendingFilters(defaultFilters);
    setPage(0);
  }, [isBackdatedTab]);

  useEffect(() => {
    fetchProjects();
    if (currentUser.role !== 'Employee') fetchUsers();
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [filters, page, rowsPerPage, fromDate, toDate, sortConfig]);

  const fetchProjects = async () => {
    const res = await api.get('/projects/');
    setProjects(res.data);
  };

  const fetchUsers = async () => {
    const res = await api.get('/users/get-users');
    setUsers(res.data);
  };

  const fetchTasks = async () => {
    const payload = {
      ...filters,
      from_date: fromDate.utc().format('YYYY-MM-DD'),
      to_date: toDate.utc().format('YYYY-MM-DD')
    };

    Object.keys(payload).forEach((key) => {
      if (payload[key] === '' || payload[key] === undefined) payload[key] = null;
    });

    const res = await api.post(`/tasks?page=${page + 1}&page_size=${rowsPerPage}&search=${search}`, payload);
    setTasks(clientSort(res.data, sortConfig));
  };

  const clientSort = (data, config) => [...data].sort((a, b) => {
    const aVal = a[config.key];
    const bVal = b[config.key];
    return config.direction === 'asc' ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1);
  });

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleConfirmAction = async () => {
    const { taskId, action } = dialog;
    try {
      if (action === 'delete') await api.delete(`/tasks/${taskId}`);
      else if (action === 'approve') await api.put(`/tasks/${taskId}/approve`);
      else if (action === 'complete') await api.put(`/tasks/${taskId}/complete`);
      fetchTasks();
    } catch (err) {
      console.error(`Failed to ${action} task`, err);
    } finally {
      setDialog({ open: false, action: null, taskId: null });
    }
  };

  const renderDialog = () => (
    <Dialog open={dialog.open} onClose={() => setDialog({ open: false })}>
      <DialogTitle>Confirm {dialog.action}</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Are you sure you want to {dialog.action} this task?
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setDialog({ open: false })}>Cancel</Button>
        <Button onClick={handleConfirmAction} autoFocus>
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );

  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      fetchTasks();
    }
  };

  const handleDownload = async () => {

    try {
      // Clean filters: convert "" to null and remove empty fields
      const cleanedFilters = Object.fromEntries(
        Object.entries(filters).map(([key, value]) => {
          if (value === "") return [key, null];  // convert empty string to null
          return [key, value];
        })
      );

      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

      const payload = {
        ...cleanedFilters,
        from_date: fromDate.utc().format('YYYY-MM-DD'),
        to_date: toDate.utc().format('YYYY-MM-DD'),
        timezone
      };
      
      const response = await api.post('/tasks/download', payload, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "task_report.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download failed", error);
    }
  };

  return (
    <Box mt={2}>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" flexWrap="wrap" gap={2}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker
              sx={{ minWidth: 250 }}
              label="From Date"
              value={fromDate}
              onChange={(newDate) => setFromDate(newDate)}
              disableFuture
              shouldDisableDate={(date) => toDate && date.isAfter(toDate)}
              slotProps={{
                textField: { size: 'small' }
              }}
            />
            <DatePicker
              sx={{ minWidth: 250 }}
              label="To Date"
              value={toDate}
              onChange={(newDate) => setToDate(newDate)}
              disableFuture
              shouldDisableDate={(date) => fromDate && date.isBefore(fromDate)}
              slotProps={{
                textField: { size: 'small' }
              }}
            />
          </LocalizationProvider>

          {/* Project Filter */}
          <FormControl size="small" sx={{ minWidth: 250 }}>
            <InputLabel shrink>Project</InputLabel>
            <Select
              name="project_id"
              value={pendingFilters.project_id || ''}
              onChange={(e) => setPendingFilters({ ...pendingFilters, project_id: e.target.value })}
              displayEmpty
              label="Project"
            >
              <MenuItem value=""><em>All</em></MenuItem>
              {projects.map(p => (
                <MenuItem key={p.id} value={p.id}>{p.project_name}</MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Status Filter */}
          <FormControl size="small" sx={{ minWidth: 250 }}>
            <InputLabel shrink>Status</InputLabel>
            <Select
              name="status"
              value={pendingFilters.status || ''}
              onChange={(e) => setPendingFilters({ ...pendingFilters, status: e.target.value })}
              displayEmpty
              label="Status"
            >
              <MenuItem value=""><em>All</em></MenuItem>
              {statusOptions.map(s => (
                <MenuItem key={s} value={s}>{s}</MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Backdated By Filter */}
          <FormControl size="small" sx={{ minWidth: 250 }}>
            <InputLabel shrink>Backdated By</InputLabel>
            <Select
              name="filter_backdated_by_creator_type"
              value={pendingFilters.filter_backdated_by_creator_type || ''}
              onChange={(e) =>
                setPendingFilters({ ...pendingFilters, filter_backdated_by_creator_type: e.target.value })
              }
              displayEmpty
              label="Backdated By"
            >
              {!isBackdatedTab && <MenuItem value=""><em>-</em></MenuItem>}
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="own">Own</MenuItem>
              <MenuItem value="manager">Manager</MenuItem>
            </Select>
          </FormControl>

          {currentUser.role !== 'Employee' && (
            <FormControl size="small" sx={{ minWidth: 250 }}>
              <InputLabel shrink>User</InputLabel>
              <Select
                name="user_id"
                value={pendingFilters.user_id || ''}
                onChange={(e) => setPendingFilters({ ...pendingFilters, user_id: e.target.value })}
                displayEmpty
                label="User"
              >
                <MenuItem value=""><em>All</em></MenuItem>
                {users.map(u => (
                  <MenuItem key={u.id} value={u.id}>
                    {u.name} ({u.role})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          <TextField
            sx={{ minWidth: 250 }}
            size="small"
            label="Search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={handleSearchKeyDown}
          />

          <Button
            variant="contained"
            color="primary"
            onClick={() => {
              setFilters({ ...pendingFilters });
              setPage(0);
            }}
          >
            Apply Filters
          </Button>

          <Button
            variant="contained"
            color="primary"
            onClick={() => {
              handleDownload();
            }}
          >
            Download Report
          </Button>
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {headers.map(header => (
                <TableCell key={header.key} onClick={() => handleSort(header.key)} sx={{ cursor: 'pointer' }}>
                  {header.label}
                  {sortConfig.key === header.key &&
                    (sortConfig.direction === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />)
                  }
                </TableCell>
              ))}
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.length === 0 ? (
              <TableRow><TableCell colSpan={headers.length + 1}><Typography align="center" color="textSecondary">No data found</Typography></TableCell></TableRow>
            ) : (
              tasks.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map(task => (
                <TableRow key={task.id}>
                  <TableCell>{dayjs(task.date).format('MM-DD-YYYY')}</TableCell>
                  <TableCell>{projects.find(p => p.id === task.project_id)?.project_name || '-'}</TableCell>
                  <TableCell>{users.find(u => u.id === task.user_id)?.name || '-'}</TableCell>
                  <TableCell>{task.task_title}</TableCell>
                  <TableCell>{dayjs(task.start_time).format('MM-DD-YYYY HH:mm')}</TableCell>
                  <TableCell>{task.end_time ? dayjs(task.end_time).format('MM-DD-YYYY HH:mm') : '-'}</TableCell>
                  <TableCell>{task.total_time_minutes ?? '-'}</TableCell>
                  <TableCell>{task.status}</TableCell>
                  <TableCell>
                    {task.status === 'In Progress' && task.user_id === currentUser.id && (
                      <Tooltip title="Mark as Done">
                        <IconButton onClick={() => setDialog({ open: true, action: 'complete', taskId: task.id })}><DoneIcon /></IconButton>
                      </Tooltip>
                    )}
                    {task.status === 'To Be Approved' &&
                      ['Manager', 'Management', 'Admin'].includes(currentUser.role) && isBackdatedTab && (
                        <Tooltip title="Approve Task">
                          <IconButton onClick={() => setDialog({ open: true, action: 'approve', taskId: task.id })}><CheckIcon /></IconButton>
                        </Tooltip>
                    )}
                    {['Manager', 'Management', 'Admin'].includes(currentUser.role) &&
                      (task.created_by === currentUser.id || task.status === 'To Be Approved') &&
                      task.status !== 'Approved' && task.status !== 'Done' && (
                        <Tooltip title="Edit Task">
                          <IconButton onClick={() => setEditTask(task)}><EditIcon /></IconButton>
                        </Tooltip>
                    )}
                    {task.created_by === currentUser.id && (
                      <Tooltip title="Delete Task">
                        <IconButton onClick={() => setDialog({ open: true, action: 'delete', taskId: task.id })}><DeleteIcon /></IconButton>
                      </Tooltip>
                    )}
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

      {renderDialog()}
    </Box>
  );
};

export default TaskTable;
