import { useQuery, useMutation } from "@tanstack/react-query";
import * as mocktest from "../services/mocktest.services";

/* CREATE */
export function useCreateMockTest() {
  return useMutation({
    mutationFn: mocktest.createMockTest
  });
}

/* DETAIL */
export function useMockTestDetail(id?:number) {
  return useQuery({
    queryKey:["mocktest", id],
    queryFn: ()=> mocktest.getMockTestDetail(id!),
    enabled: !!id
  });
}

/* SUBMIT ANSWER */
export function useSubmitAnswer() {
  return useMutation({
    mutationFn: mocktest.submitAnswer
  });
}

/* RESULTS */
export function useResults() {
  return useQuery({
    queryKey:["results"],
    queryFn: mocktest.getResults
  });
}

/* GENERATE PRACTICE */
export function useGeneratePractice() {
  return useMutation({
    mutationFn: mocktest.generatePractice
  });
}