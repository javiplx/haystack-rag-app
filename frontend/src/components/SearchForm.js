import React from 'react';
import { Form, Button } from 'react-bootstrap';

function SearchForm({ query, setQuery, onSubmit }) {
  return (
    <Form onSubmit={onSubmit} role="form">
      <Form.Group className="mb-3" controlId="formQuery">
        <Form.Control
          type="text"
          placeholder="Type your question here"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </Form.Group>
      <Button variant="primary" type="submit" className="w-100">
        Submit
      </Button>
    </Form>
  );
}

export default SearchForm;
