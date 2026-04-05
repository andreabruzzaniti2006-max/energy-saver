import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  withCredentials: true,
});

export const formatCurrency = (value) => {
  const number = Number(value || 0);
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2,
  }).format(number);
};

export const formatNumber = (value, options = {}) =>
  new Intl.NumberFormat("it-IT", {
    maximumFractionDigits: 1,
    ...options,
  }).format(Number(value || 0));

export const formatDateTime = (value) => {
  if (!value) return "—";
  return new Intl.DateTimeFormat("it-IT", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
};

export const formatDate = (value) => {
  if (!value) return "—";
  return new Intl.DateTimeFormat("it-IT", {
    dateStyle: "medium",
  }).format(new Date(value));
};

export const extractApiError = (error, fallback = "Si è verificato un errore") => {
  return error?.response?.data?.detail || fallback;
};
