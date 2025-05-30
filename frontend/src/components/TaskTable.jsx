import React from 'react'
import { Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material'

const TaskTable = ({ tasks }) => {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell>Title</TableCell>
          <TableCell>Project</TableCell>
          <TableCell>Start</TableCell>
          <TableCell>End</TableCell>
          <TableCell>Status</TableCell>
          <TableCell>Total Time</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {tasks.map((task, idx) => (
          <TableRow key={idx}>
            <TableCell>{task.task_title}</TableCell>
            <TableCell>{task.project_id}</TableCell>
            <TableCell>{new Date(task.start_time).toLocaleString()}</TableCell>
            <TableCell>{task.end_time ? new Date(task.end_time).toLocaleString() : '-'}</TableCell>
            <TableCell>{task.status}</TableCell>
            <TableCell>{task.total_time_minutes ?? '-'}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export default TaskTable
